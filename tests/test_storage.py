import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir, closing
from pathlib import Path
from sqlite3 import connect
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

from pos.container import Container
from pos.domain.catalog import Student
from pos.settings import Settings


class StorageTests(TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        self.database_path = Path(directory) / "nested" / "assessment.sqlite3"
        self.container = Container(self.database_path)
        self.container.initialize()

    def test_write_transaction_rolls_back(self) -> None:
        student = Student(uuid4(), "Анна Волкова")
        with (
            self.assertRaisesRegex(RuntimeError, "rollback"),
            self.container.storage.transaction(write=True) as tx,
        ):
            tx.students.save(student)
            raise RuntimeError("rollback")
        self.assertEqual(self.container.students.list_students(), [])

    def test_read_transaction_keeps_snapshot(self) -> None:
        with self.container.storage.transaction() as tx:
            self.assertEqual(tx.students.list(), [])
            student = self.container.students.add_student("Анна Волкова")
            self.assertEqual(tx.students.list(), [])
        self.assertEqual(self.container.students.list_students(), [student])

    def test_parallel_start_initializes_fresh_database(self) -> None:
        database = self.database_path.with_name("fresh.sqlite3")
        containers = [Container(database) for _ in range(4)]
        ready = Barrier(len(containers))

        def initialize(container: Container) -> None:
            ready.wait(timeout=5)
            container.initialize()

        with ThreadPoolExecutor(max_workers=len(containers)) as executor:
            list(executor.map(initialize, containers))
        self.assertEqual(containers[0].students.list_students(), [])

    def test_start_retries_wal_transition_after_reader_releases_lock(self) -> None:
        database = self.database_path.with_name("before-wal.sqlite3")
        container = Container(database)
        with closing(connect(database, isolation_level=None)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT name FROM sqlite_master").fetchall()

            def release_reader(_: float) -> None:
                reader.execute("ROLLBACK")

            with patch("pos.adapters.sqlite.storage.sleep", side_effect=release_reader) as retry:
                container.initialize()
            retry.assert_called_once()
        with closing(connect(database)) as fresh_reader:
            self.assertEqual(fresh_reader.execute("PRAGMA journal_mode").fetchone(), ("wal",))


class SettingsTests(TestCase):
    def test_settings_read_dotenv_and_prefer_environment(self) -> None:
        directory = Path(self.enterContext(TemporaryDirectory()))
        database = directory / "assessment.sqlite3"
        env_file = directory / ".env"
        env_file.write_text(
            f"POS_DB_PATH='{database}'\nPOS_DB_TIMEOUT=3.5\nPOS_API_PORT=8123\n",
            encoding="utf-8",
        )
        with chdir(directory), patch.dict(os.environ, {"POS_API_PORT": "8124"}, clear=True):
            settings = Settings()
        self.assertEqual(settings.db_path, database)
        self.assertEqual(settings.db_timeout, 3.5)
        self.assertEqual(settings.api_port, 8124)
        self.assertEqual(settings.api_host, "127.0.0.1")
