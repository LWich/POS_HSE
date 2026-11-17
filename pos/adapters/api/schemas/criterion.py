from decimal import Decimal
from uuid import UUID

from pos.adapters.api.schemas.base import InputModel, View


class CriterionInput(InputModel):
    name: str
    max_score: Decimal
    weight: Decimal


class CriterionView(View):
    id: UUID
    name: str
    max_score: Decimal
    weight: Decimal
