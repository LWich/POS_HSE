import os
import subprocess  # noqa: S404 - tests invoke the local Python interpreter without a shell
import sys
from csv import DictReader
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


class CliTests(TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        self.database = Path(directory) / "cli.sqlite3"

    def cli(self, *args: str, exit_code: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(  # noqa: S603 - fixed interpreter and module, no shell
            [sys.executable, "-m", "pos.adapters.cli", *args],
            env={**os.environ, "POS_DB_PATH": str(self.database)},
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(result.returncode, exit_code, result.stderr)
        return result

    def test_grade_workflow_persists_between_commands(self) -> None:
        self.assertIn("Список пуст", self.cli("students", "list").stdout)
        student = self.cli("students", "add", "Анна Волкова").stdout.split()[0]
        criterion = self.cli("criteria", "add", "Практика", "10", "60").stdout.split()[0]
        self.assertIn(student, self.cli("students", "list").stdout)
        self.assertIn(criterion, self.cli("criteria", "list").stdout)

        bad_number = self.cli("grades", "add", student, criterion, "abc", exit_code=2)
        self.assertIn("Укажите число", bad_number.stderr)
        too_high = self.cli("grades", "add", student, criterion, "12", exit_code=1)
        self.assertIn("от 0 до 10", too_high.stderr)
        self.assertIn("Список пуст", self.cli("grades", "list", student).stdout)

        self.cli("grades", "add", student, criterion, "8.5", "--comment", "Проверено")
        self.assertIn("8.5/10", self.cli("grades", "list", student).stdout)
        self.cli("grades", "update", student, criterion, "7")
        self.assertIn("7.00/10", self.cli("result", student).stdout)
        self.assertIn("средний балл 7.00", self.cli("analytics").stdout)
        exported = self.cli("export").stdout.removeprefix("\ufeff")
        (row,) = DictReader(StringIO(exported))
        self.assertEqual(row["student_id"], student)
        self.assertEqual(row["total_out_of_10"], "7.00")

        self.cli("grades", "delete", student, criterion)
        self.assertIn("оценено 0/1", self.cli("results").stdout)
        self.cli("criteria", "delete", criterion)
        self.cli("students", "delete", student)

    def test_demo_outputs_csv_without_touching_main_store(self) -> None:
        demo = self.cli("demo").stdout
        self.assertFalse(self.database.exists())
        csv_text = demo.split("4. CSV-выгрузка\n", maxsplit=1)[1]
        results = {row["student_name"]: row["total_out_of_10"] for row in DictReader(StringIO(csv_text))}
        self.assertEqual(results, {"Анна Волкова": "7.70", "Иван Ким": "4.00"})
