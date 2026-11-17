from uuid import UUID

from fastapi import APIRouter

from pos.adapters.api.decimal_route import DecimalRoute
from pos.adapters.api.dependencies import CriteriaDep
from pos.adapters.api.schemas.criterion import CriterionInput, CriterionView
from pos.domain.catalog import Criterion

router = APIRouter(prefix="/criteria", tags=["Рубрикатор"], route_class=DecimalRoute)


@router.get("", response_model=list[CriterionView], summary="Показать рубрикатор")
def list_criteria(service: CriteriaDep) -> tuple[Criterion, ...]:
    return service.list_criteria()


@router.post("", response_model=CriterionView, status_code=201, summary="Добавить критерий")
def add_criterion(body: CriterionInput, service: CriteriaDep) -> Criterion:
    return service.add_criterion(body.name, body.max_score, body.weight)


@router.get("/{criterion_id}", response_model=CriterionView, summary="Найти критерий")
def get_criterion(criterion_id: UUID, service: CriteriaDep) -> Criterion:
    return service.get_criterion(criterion_id)


@router.put("/{criterion_id}", response_model=CriterionView, summary="Изменить критерий")
def update_criterion(criterion_id: UUID, body: CriterionInput, service: CriteriaDep) -> Criterion:
    return service.update_criterion(criterion_id, body.name, body.max_score, body.weight)


@router.delete("/{criterion_id}", status_code=204, summary="Удалить критерий")
def delete_criterion(criterion_id: UUID, service: CriteriaDep) -> None:
    service.delete_criterion(criterion_id)
