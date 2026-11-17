from dataclasses import replace
from decimal import Decimal
from uuid import UUID, uuid4

from pos.application.ports import UnitOfWork
from pos.domain.catalog import Criterion
from pos.domain.errors import ConflictError


class CriteriaService:
    def __init__(self, storage: UnitOfWork) -> None:
        self._storage = storage

    def add_criterion(self, name: str, max_score: Decimal, weight: Decimal) -> Criterion:
        criterion = Criterion(uuid4(), name, max_score, weight)
        with self._storage.transaction(write=True) as tx:
            tx.rubric.get().check_criterion_name(criterion)
            tx.rubric.save(criterion)
        return criterion

    def list_criteria(self) -> tuple[Criterion, ...]:
        with self._storage.transaction() as tx:
            return tx.rubric.get().criteria

    def get_criterion(self, criterion_id: UUID) -> Criterion:
        with self._storage.transaction() as tx:
            return tx.rubric.get().require(criterion_id)

    def update_criterion(
        self,
        criterion_id: UUID,
        name: str,
        max_score: Decimal,
        weight: Decimal,
    ) -> Criterion:
        with self._storage.transaction(write=True) as tx:
            rubric = tx.rubric.get()
            current = rubric.require(criterion_id)
            updated = replace(current, name=name, max_score=max_score, weight=weight)
            rubric.check_criterion_name(updated)
            evaluations = tx.evaluations.list(criterion_id=criterion_id)
            if any(not updated.accepts_score(evaluation.score) for evaluation in evaluations):
                raise ConflictError("Новый максимум ниже одной из выставленных оценок.")
            tx.rubric.save(updated)
        return updated

    def delete_criterion(self, criterion_id: UUID) -> None:
        with self._storage.transaction(write=True) as tx:
            tx.rubric.get().require(criterion_id)
            if tx.evaluations.exists(criterion_id=criterion_id):
                raise ConflictError("Перед удалением критерия отмените выставленные по нему оценки.")
            tx.rubric.delete(criterion_id)
