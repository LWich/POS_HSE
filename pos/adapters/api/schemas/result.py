from decimal import Decimal
from uuid import UUID

from pos.adapters.api.schemas.base import View


class ResultView(View):
    student_id: UUID
    student_name: str
    total: Decimal | None
    graded_count: int
    criteria_count: int
    missing_criterion_ids: tuple[UUID, ...]
