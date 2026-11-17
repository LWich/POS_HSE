from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from uuid import UUID

from pos.domain.catalog import Rubric
from pos.domain.evaluation import Evaluation
from pos.domain.result import StudentResult, round_to_hundredths


@dataclass(frozen=True, slots=True)
class CriterionAnalytics:
    criterion_id: UUID
    name: str
    max_score: Decimal
    graded_count: int
    missing_count: int
    average_score: Decimal | None


@dataclass(frozen=True, slots=True)
class CourseAnalytics:
    student_count: int
    criteria_count: int
    graded_count: int
    average_total: Decimal | None
    criteria: tuple[CriterionAnalytics, ...]


def mean(values: list[Decimal]) -> Decimal | None:
    if values:
        return round_to_hundredths(sum(map(Fraction, values), Fraction()) / len(values))
    return None


def summarize(
    rubric: Rubric,
    results: list[StudentResult],
    evaluations: list[Evaluation],
) -> CourseAnalytics:
    scores: dict[UUID, list[Decimal]] = defaultdict(list)
    for evaluation in evaluations:
        scores[evaluation.criterion_id].append(evaluation.score.value)

    criteria = []
    for criterion in rubric.criteria:
        criterion_scores = scores[criterion.id]
        criteria.append(
            CriterionAnalytics(
                criterion.id,
                criterion.name,
                criterion.max_score,
                len(criterion_scores),
                len(results) - len(criterion_scores),
                mean(criterion_scores),
            )
        )
    totals = [result.total for result in results if result.total is not None]
    return CourseAnalytics(len(results), len(criteria), len(evaluations), mean(totals), tuple(criteria))
