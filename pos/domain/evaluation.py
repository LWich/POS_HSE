from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pos.domain.catalog import Criterion, Rubric, Student
from pos.domain.errors import InvalidValueError
from pos.domain.values import Score


@dataclass(frozen=True, slots=True)
class Evaluation:
    student_id: UUID
    criterion: Criterion
    score: Score
    evaluated_at: datetime
    updated_at: datetime
    comment: str | None = None

    def __post_init__(self) -> None:
        self.criterion.check_score(self.score)
        if self.comment is not None:
            comment = self.comment.strip()
            if len(comment) > 1000:
                raise InvalidValueError("Комментарий допускает до 1000 символов.")
            object.__setattr__(self, "comment", comment or None)

    @property
    def criterion_id(self) -> UUID:
        return self.criterion.id


class EvaluationFactory:
    def __init__(self, clock: Callable[[], datetime]) -> None:
        self._clock = clock

    def issue(
        self,
        student: Student,
        rubric: Rubric,
        criterion_id: UUID,
        score: Decimal,
        comment: str | None,
    ) -> Evaluation:
        criterion = rubric.require(criterion_id)
        now = self._clock()
        return Evaluation(student.id, criterion, Score(score), now, now, comment)

    def correct(
        self,
        evaluation: Evaluation,
        rubric: Rubric | None,
        score: Decimal,
        comment: str | None,
    ) -> Evaluation:
        criterion = evaluation.criterion if rubric is None else rubric.require(evaluation.criterion_id)
        return replace(
            evaluation,
            criterion=criterion,
            score=Score(score),
            updated_at=self._clock(),
            comment=comment,
        )
