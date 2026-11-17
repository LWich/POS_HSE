from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ColumnElement, delete, exists, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from pos.adapters.sqlite.models.criterion import CriterionRow
from pos.adapters.sqlite.models.evaluation import EvaluationRow
from pos.adapters.sqlite.models.student import StudentRow
from pos.domain.catalog import Criterion, Rubric, Student
from pos.domain.evaluation import Evaluation
from pos.domain.values import Score


def as_student(row: StudentRow) -> Student:
    return Student(UUID(row.id), row.name)


def as_criterion(row: CriterionRow) -> Criterion:
    return Criterion(UUID(row.id), row.name, Decimal(row.max_score), Decimal(row.weight))


def as_evaluation(row: EvaluationRow, criterion: CriterionRow) -> Evaluation:
    return Evaluation(
        UUID(row.student_id),
        as_criterion(criterion),
        Score(Decimal(row.score)),
        datetime.fromisoformat(row.evaluated_at),
        datetime.fromisoformat(row.updated_at),
        row.comment,
    )


def evaluation_filters(student_id: UUID | None, criterion_id: UUID | None) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []
    if student_id is not None:
        filters.append(EvaluationRow.student_id == str(student_id))
    if criterion_id is not None:
        filters.append(EvaluationRow.criterion_id == str(criterion_id))
    return filters


class SQLiteStudents:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, student_id: UUID) -> Student | None:
        row = self._session.get(StudentRow, str(student_id))
        return as_student(row) if row is not None else None

    def list(self) -> list[Student]:
        rows = self._session.scalars(select(StudentRow).order_by(StudentRow.name, StudentRow.id))
        return [as_student(row) for row in rows]

    def save(self, student: Student) -> None:
        statement = insert(StudentRow).values(id=str(student.id), name=student.name)
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[StudentRow.id], set_={"name": statement.excluded.name}
            )
        )

    def delete(self, student_id: UUID) -> None:
        self._session.execute(delete(StudentRow).where(StudentRow.id == str(student_id)))


class SQLiteRubric:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> Rubric:
        rows = self._session.scalars(
            select(CriterionRow).order_by(CriterionRow.name_key, CriterionRow.id)
        )
        return Rubric(tuple(as_criterion(row) for row in rows))

    def save(self, criterion: Criterion) -> None:
        statement = insert(CriterionRow).values(
            id=str(criterion.id),
            name=criterion.name,
            name_key=criterion.name_key,
            max_score=format(criterion.max_score, "f"),
            weight=format(criterion.weight, "f"),
        )
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[CriterionRow.id],
                set_={
                    "name": statement.excluded.name,
                    "name_key": statement.excluded.name_key,
                    "max_score": statement.excluded.max_score,
                    "weight": statement.excluded.weight,
                },
            )
        )

    def delete(self, criterion_id: UUID) -> None:
        self._session.execute(delete(CriterionRow).where(CriterionRow.id == str(criterion_id)))


class SQLiteEvaluations:
    _select = select(EvaluationRow, CriterionRow).join(CriterionRow)

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, student_id: UUID, criterion_id: UUID) -> Evaluation | None:
        rows = self._session.execute(self._select.where(*evaluation_filters(student_id, criterion_id)))
        row = rows.one_or_none()
        if row is None:
            return None
        evaluation, criterion = row
        return as_evaluation(evaluation, criterion)

    def exists(self, *, student_id: UUID | None = None, criterion_id: UUID | None = None) -> bool:
        matching = (
            exists().select_from(EvaluationRow).where(*evaluation_filters(student_id, criterion_id))
        )
        return bool(self._session.scalar(select(matching)))

    def list(
        self,
        *,
        student_id: UUID | None = None,
        criterion_id: UUID | None = None,
    ) -> list[Evaluation]:
        query = self._select.where(*evaluation_filters(student_id, criterion_id))
        rows = self._session.execute(query.order_by(CriterionRow.name_key, EvaluationRow.student_id))
        return [as_evaluation(evaluation, criterion) for evaluation, criterion in rows]

    def save(self, evaluation: Evaluation) -> None:
        statement = insert(EvaluationRow).values(
            student_id=str(evaluation.student_id),
            criterion_id=str(evaluation.criterion_id),
            score=format(evaluation.score.value, "f"),
            evaluated_at=evaluation.evaluated_at.isoformat(),
            updated_at=evaluation.updated_at.isoformat(),
            comment=evaluation.comment,
        )
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[EvaluationRow.student_id, EvaluationRow.criterion_id],
                set_={
                    "score": statement.excluded.score,
                    "updated_at": statement.excluded.updated_at,
                    "comment": statement.excluded.comment,
                },
            )
        )

    def delete(self, student_id: UUID, criterion_id: UUID) -> None:
        self._session.execute(delete(EvaluationRow).where(*evaluation_filters(student_id, criterion_id)))
