from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

from pos.domain.catalog import Rubric, Student
from pos.domain.evaluation import Evaluation


@dataclass(frozen=True, slots=True)
class StudentResult:
    student_id: UUID
    student_name: str
    total: Decimal | None
    graded_count: int
    criteria_count: int
    missing_criterion_ids: tuple[UUID, ...]


def round_to_hundredths(value: Fraction) -> Decimal:
    cents, remainder = divmod(value.numerator * 100, value.denominator)
    if remainder * 2 >= value.denominator:
        cents += 1
    return Decimal(f"{cents}e-2")


class ResultCalculator:
    """Переводит оценки по текущему рубрикатору в общий балл из 10"""

    def calculate(
        self,
        student: Student,
        rubric: Rubric,
        evaluations: Iterable[Evaluation],
    ) -> StudentResult:
        scores = {
            evaluation.criterion_id: evaluation.score
            for evaluation in evaluations
            if evaluation.student_id == student.id
        }
        weight_sum = Fraction()
        weighted_score = Fraction()
        missing = []
        for criterion in rubric.criteria:
            weight = Fraction(criterion.weight)
            weight_sum += weight
            score = scores.get(criterion.id)
            if score is None:
                missing.append(criterion.id)
                continue
            criterion.check_score(score)
            weighted_score += weight * Fraction(score.value) / Fraction(criterion.max_score)

        count = len(rubric.criteria)
        total = round_to_hundredths(10 * weighted_score / weight_sum) if count else None
        return StudentResult(
            student.id, student.name, total, count - len(missing), count, tuple(missing)
        )
