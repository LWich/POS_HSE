import sys
from collections.abc import Callable, Sequence
from decimal import Decimal

from pos.adapters.csv_export import results_csv
from pos.application.analytics import CourseAnalytics
from pos.domain.catalog import Criterion, Student
from pos.domain.evaluation import Evaluation
from pos.domain.result import StudentResult


def score_text(value: Decimal | None) -> str:
    return format(value, "f") if value is not None else "—"


def show_student(student: Student) -> None:
    print(f"{student.id}  {student.name}")


def show_criterion(criterion: Criterion) -> None:
    print(
        f"{criterion.id}  {criterion.name}  максимум {criterion.max_score:f}  вес {criterion.weight:f}"
    )


def show_evaluation(evaluation: Evaluation) -> None:
    criterion = evaluation.criterion
    comment = f"  {evaluation.comment!r}" if evaluation.comment else ""
    print(
        f"{criterion.id}  {criterion.name}  {evaluation.score.value:f}/{criterion.max_score:f}{comment}"
    )


def show_result(result: StudentResult) -> None:
    total = f"{result.total:f}/10" if result.total is not None else "рубрикатор пуст"
    print(
        f"{result.student_id}  {result.student_name}  {total}  "
        f"оценено {result.graded_count}/{result.criteria_count}"
    )


def show_list[T](show_item: Callable[[T], None]) -> Callable[[Sequence[T]], None]:
    def show_items(items: Sequence[T]) -> None:
        if not items:
            print("Список пуст.")
        for item in items:
            show_item(item)

    return show_items


def show_deleted(_: None) -> None:
    print("Запись удалена.")


def show_analytics(analytics: CourseAnalytics) -> None:
    print(
        f"Студентов {analytics.student_count}, критериев {analytics.criteria_count}, "
        f"оценок {analytics.graded_count}, средний итог {score_text(analytics.average_total)}."
    )
    for criterion in analytics.criteria:
        print(
            f"{criterion.name}  средний балл {score_text(criterion.average_score)} "
            f"из {criterion.max_score:f}  выставлено {criterion.graded_count}  "
            f"пропущено {criterion.missing_count}"
        )


def write_csv(results: list[StudentResult]) -> None:
    sys.stdout.buffer.write(results_csv(results))
