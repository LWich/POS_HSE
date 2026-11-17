import argparse
from collections.abc import Callable
from decimal import Decimal, InvalidOperation
from functools import partial
from uuid import UUID

from pos.adapters.cli.demo import run_demo
from pos.adapters.cli.presentation import (
    show_analytics,
    show_criterion,
    show_deleted,
    show_evaluation,
    show_list,
    show_result,
    show_student,
    write_csv,
)
from pos.application.services.criteria import CriteriaService
from pos.application.services.evaluations import EvaluationsService
from pos.application.services.reports import ReportsService
from pos.application.services.students import StudentsService
from pos.container import Container

type Subcommands = argparse._SubParsersAction[argparse.ArgumentParser]


def decimal_arg(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("Укажите число с точкой, например 8.5.") from error


ARGUMENTS: dict[str, tuple[Callable[[str], object], str]] = {
    "student_id": (UUID, "ID_СТУДЕНТА"),
    "criterion_id": (UUID, "ID_КРИТЕРИЯ"),
    "name": (str, "НАЗВАНИЕ"),
    "max_score": (decimal_arg, "МАКС_БАЛЛ"),
    "weight": (decimal_arg, "ВЕС"),
    "score": (decimal_arg, "БАЛЛ"),
}


def execute[T](
    get_service: Callable[[Container], object],
    method: Callable[..., T],
    output: Callable[[T], None],
    parameters: tuple[str, ...],
    arguments: argparse.Namespace,
) -> None:
    container = Container()
    container.initialize()
    args = [getattr(arguments, name) for name in parameters]
    output(method(get_service(container), *args))


def command[T](
    actions: Subcommands,
    get_service: Callable[[Container], object],
    name: str,
    help_text: str,
    method: Callable[..., T],
    output: Callable[[T], None],
    *parameters: str,
) -> None:
    parser = actions.add_parser(name, help=help_text, description=help_text)
    for parameter in parameters:
        if parameter == "comment":
            parser.add_argument("--comment", help="Комментарий к оценке")
        else:
            converter, metavar = ARGUMENTS[parameter]
            parser.add_argument(parameter, type=converter, metavar=metavar)
    parser.set_defaults(handler=partial(execute, get_service, method, output, parameters))


def register_students(actions: Subcommands) -> None:
    students = actions.add_parser("students", help="Студенты").add_subparsers(required=True)

    register = partial(command, students, lambda container: container.students)
    register("list", "Список студентов", StudentsService.list_students, show_list(show_student))
    register("add", "Добавить студента", StudentsService.add_student, show_student, "name")
    register("get", "Показать студента", StudentsService.get_student, show_student, "student_id")
    register(
        "update", "Изменить имя", StudentsService.update_student, show_student, "student_id", "name"
    )
    register("delete", "Удалить студента", StudentsService.delete_student, show_deleted, "student_id")


def register_criteria(actions: Subcommands) -> None:
    criteria = actions.add_parser("criteria", help="Рубрикатор").add_subparsers(required=True)

    register = partial(command, criteria, lambda container: container.criteria)
    register("list", "Список критериев", CriteriaService.list_criteria, show_list(show_criterion))
    register(
        "add",
        "Добавить критерий",
        CriteriaService.add_criterion,
        show_criterion,
        "name",
        "max_score",
        "weight",
    )
    register("get", "Показать критерий", CriteriaService.get_criterion, show_criterion, "criterion_id")
    register(
        "update",
        "Изменить критерий",
        CriteriaService.update_criterion,
        show_criterion,
        "criterion_id",
        "name",
        "max_score",
        "weight",
    )
    register(
        "delete", "Удалить критерий", CriteriaService.delete_criterion, show_deleted, "criterion_id"
    )


def register_grades(actions: Subcommands) -> None:
    grades = actions.add_parser("grades", help="Оценки").add_subparsers(required=True)

    register = partial(command, grades, lambda container: container.evaluations)
    register(
        "list",
        "Оценки студента",
        EvaluationsService.list_evaluations,
        show_list(show_evaluation),
        "student_id",
    )
    register(
        "get",
        "Показать оценку",
        EvaluationsService.get_evaluation,
        show_evaluation,
        "student_id",
        "criterion_id",
    )
    register(
        "add",
        "Выставить оценку",
        EvaluationsService.issue_evaluation,
        show_evaluation,
        "student_id",
        "criterion_id",
        "score",
        "comment",
    )
    register(
        "update",
        "Исправить оценку",
        EvaluationsService.correct_evaluation,
        show_evaluation,
        "student_id",
        "criterion_id",
        "score",
        "comment",
    )
    register(
        "delete",
        "Отменить оценку",
        EvaluationsService.cancel_evaluation,
        show_deleted,
        "student_id",
        "criterion_id",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pos", description="Преподавательская оценка студентов")
    actions = parser.add_subparsers(required=True)
    register_students(actions)
    register_criteria(actions)
    register_grades(actions)

    register = partial(command, actions, lambda container: container.reports)
    register("result", "Итог студента", ReportsService.get_result, show_result, "student_id")
    register("results", "Итоги по курсу", ReportsService.list_results, show_list(show_result))
    register("analytics", "Аналитика по курсу", ReportsService.analytics, show_analytics)
    register("export", "Выгрузить CSV в stdout", ReportsService.list_results, write_csv)
    actions.add_parser("demo", help="Демонстрация на отдельной базе").set_defaults(handler=run_demo)
    return parser
