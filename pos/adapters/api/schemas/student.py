from uuid import UUID

from pos.adapters.api.schemas.base import InputModel, View


class StudentInput(InputModel):
    name: str


class StudentView(View):
    id: UUID
    name: str
