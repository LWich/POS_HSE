from argparse import Namespace
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from pos.adapters.cli.presentation import show_criterion, show_evaluation, show_result, show_student
from pos.adapters.csv_export import results_csv
from pos.container import Container


def run_demo(_: Namespace) -> None:
    with TemporaryDirectory() as directory:
        container = Container(Path(directory) / "demo.sqlite3")
        container.initialize()
        print("1. Студенты и рубрикатор")
        anna = container.students.add_student("Анна Волкова")
        ivan = container.students.add_student("Иван Ким")
        practice = container.criteria.add_criterion("Практика", Decimal(10), Decimal(40))
        project = container.criteria.add_criterion("Проект", Decimal(20), Decimal(60))
        for student in (anna, ivan):
            show_student(student)
        for criterion in (practice, project):
            show_criterion(criterion)

        print("\n2. Выставление оценок")
        for student, criterion, value in (
            (anna, practice, 8),
            (anna, project, 15),
            (ivan, practice, 10),
        ):
            print(student.name)
            show_evaluation(
                container.evaluations.issue_evaluation(student.id, criterion.id, Decimal(value))
            )

        print("\n3. Взвешенные итоги")
        results = container.reports.list_results()
        for result in results:
            show_result(result)

        print("\n4. CSV-выгрузка")
        print(results_csv(results).decode("utf-8-sig"), end="")
