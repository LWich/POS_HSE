from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from pos.adapters.api.schemas.base import InputModel
from pos.domain.evaluation import Evaluation


class ScoreInput(InputModel):
    score: Decimal
    comment: str | None = None


class EvaluationInput(ScoreInput):
    criterion_id: UUID


class EvaluationView(BaseModel):
    student_id: UUID
    criterion_id: UUID
    criterion_name: str
    max_score: Decimal
    score: Decimal
    evaluated_at: datetime
    updated_at: datetime
    comment: str | None

    @classmethod
    def from_evaluation(cls, evaluation: Evaluation) -> "EvaluationView":
        return cls(
            student_id=evaluation.student_id,
            criterion_id=evaluation.criterion_id,
            criterion_name=evaluation.criterion.name,
            max_score=evaluation.criterion.max_score,
            score=evaluation.score.value,
            evaluated_at=evaluation.evaluated_at,
            updated_at=evaluation.updated_at,
            comment=evaluation.comment,
        )
