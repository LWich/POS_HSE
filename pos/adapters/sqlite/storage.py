from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import LEGACY_TRANSACTION_CONTROL, SQLITE_BUSY
from sqlite3 import Connection as SQLiteConnection
from sqlite3 import OperationalError as SQLiteOperationalError
from time import monotonic, sleep

from sqlalchemy import URL, Connection, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry, NullPool

from pos.adapters.sqlite.models.base import Base
from pos.adapters.sqlite.repositories import SQLiteEvaluations, SQLiteRubric, SQLiteStudents
from pos.application.ports import EvaluationRepository, RubricRepository, StudentRepository, Transaction


@dataclass(slots=True)
class SQLiteTransaction:
    students: StudentRepository
    rubric: RubricRepository
    evaluations: EvaluationRepository


def enable_foreign_keys(connection: SQLiteConnection, _: ConnectionPoolEntry) -> None:
    with closing(connection.cursor()) as cursor:
        cursor.execute("PRAGMA foreign_keys = ON")


def begin_transaction(connection: Connection) -> None:
    if connection.get_execution_options().get("sqlite_write"):
        connection.exec_driver_sql("BEGIN IMMEDIATE")
    else:
        connection.exec_driver_sql("BEGIN")


class SQLiteUnitOfWork:
    def __init__(self, database_path: Path, *, timeout: float) -> None:
        self._database_path = database_path
        self._timeout = timeout
        self._engine = create_engine(
            URL.create("sqlite+pysqlite", database=str(database_path)),
            connect_args={
                "timeout": timeout,
                "autocommit": LEGACY_TRANSACTION_CONTROL,
                "isolation_level": None,
            },
            poolclass=NullPool,
        )
        event.listen(self._engine, "connect", enable_foreign_keys)
        event.listen(self._engine, "begin", begin_transaction)
        self._sessions = sessionmaker(self._engine)

    def initialize(self) -> None:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._enable_wal()
        with (
            self._engine.connect().execution_options(sqlite_write=True) as connection,
            connection.begin(),
        ):
            Base.metadata.create_all(connection)

    def _enable_wal(self) -> None:
        deadline = monotonic() + self._timeout
        with (
            closing(self._engine.raw_connection()) as connection,
            closing(connection.cursor()) as cursor,
        ):
            # Use one deadline for all WAL attempts on this connection
            cursor.execute("PRAGMA busy_timeout = 0")
            while True:
                try:
                    cursor.execute("PRAGMA journal_mode = WAL")
                    cursor.fetchone()
                    return
                except SQLiteOperationalError as error:
                    remaining = deadline - monotonic()
                    if error.sqlite_errorcode & 0xFF != SQLITE_BUSY or remaining <= 0:
                        raise
                    sleep(min(remaining, 0.05))

    @contextmanager
    def transaction(self, *, write: bool = False) -> Iterator[Transaction]:
        with self._sessions.begin() as session:
            session.connection(execution_options={"sqlite_write": write})
            yield SQLiteTransaction(
                SQLiteStudents(session),
                SQLiteRubric(session),
                SQLiteEvaluations(session),
            )
