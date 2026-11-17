from decimal import Decimal
from uuid import UUID

from pos.adapters.api.schemas.base import View


class CriterionAnalyticsView(View):
    criterion_id: UUID
    name: str
    max_score: Decimal
    graded_count: int
    missing_count: int
    average_score: Decimal | None


class AnalyticsView(View):
    student_count: int
    criteria_count: int
    graded_count: int
    average_total: Decimal | None
    criteria: tuple[CriterionAnalyticsView, ...]
