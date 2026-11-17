from decimal import Decimal
from uuid import UUID

from pos.application.ports import Transaction, UnitOfWork
from pos.application.services.students import require_student
from pos.domain.errors import ConflictError, NotFoundError
from pos.domain.evaluation import Evaluation, EvaluationFactory


def require_evaluation(tx: Transaction, student_id: UUID, criterion_id: UUID) -> Evaluation:
    require_student(tx, student_id)
    evaluation = tx.evaluations.get(student_id, criterion_id)
    if evaluation is None:
        raise NotFoundError("Оценка по этому критерию не выставлена.")
    return evaluation


class EvaluationsService:
    def __init__(self, storage: UnitOfWork, factory: EvaluationFactory) -> None:
        self._storage = storage
        self._factory = factory

    def issue_evaluation(
        self,
        student_id: UUID,
        criterion_id: UUID,
        score: Decimal,
        comment: str | None = None,
    ) -> Evaluation:
        with self._storage.transaction(write=True) as tx:
            student = require_student(tx, student_id)
            if tx.evaluations.exists(student_id=student_id, criterion_id=criterion_id):
                raise ConflictError("Оценка уже выставлена. Используйте исправление.")
            evaluation = self._factory.issue(student, tx.rubric.get(), criterion_id, score, comment)
            tx.evaluations.save(evaluation)
        return evaluation

    def list_evaluations(self, student_id: UUID) -> list[Evaluation]:
        with self._storage.transaction() as tx:
            require_student(tx, student_id)
            return tx.evaluations.list(student_id=student_id)

    def get_evaluation(self, student_id: UUID, criterion_id: UUID) -> Evaluation:
        with self._storage.transaction() as tx:
            return require_evaluation(tx, student_id, criterion_id)

    def correct_evaluation(
        self,
        student_id: UUID,
        criterion_id: UUID,
        score: Decimal,
        comment: str | None = None,
    ) -> Evaluation:
        with self._storage.transaction(write=True) as tx:
            previous = require_evaluation(tx, student_id, criterion_id)
            # The repository joins the current criterion in the same transaction
            evaluation = self._factory.correct(previous, rubric=None, score=score, comment=comment)
            tx.evaluations.save(evaluation)
        return evaluation

    def cancel_evaluation(self, student_id: UUID, criterion_id: UUID) -> None:
        with self._storage.transaction(write=True) as tx:
            require_evaluation(tx, student_id, criterion_id)
            tx.evaluations.delete(student_id, criterion_id)
