from dataclasses import replace
from uuid import UUID, uuid4

from pos.application.ports import Transaction, UnitOfWork
from pos.domain.catalog import Student
from pos.domain.errors import ConflictError, NotFoundError


def require_student(tx: Transaction, student_id: UUID) -> Student:
    student = tx.students.get(student_id)
    if student is None:
        raise NotFoundError(f"Студент {student_id} не найден.")
    return student


class StudentsService:
    def __init__(self, storage: UnitOfWork) -> None:
        self._storage = storage

    def add_student(self, name: str) -> Student:
        student = Student(uuid4(), name)
        with self._storage.transaction(write=True) as tx:
            tx.students.save(student)
        return student

    def list_students(self) -> list[Student]:
        with self._storage.transaction() as tx:
            return tx.students.list()

    def get_student(self, student_id: UUID) -> Student:
        with self._storage.transaction() as tx:
            return require_student(tx, student_id)

    def update_student(self, student_id: UUID, name: str) -> Student:
        with self._storage.transaction(write=True) as tx:
            student = replace(require_student(tx, student_id), name=name)
            tx.students.save(student)
        return student

    def delete_student(self, student_id: UUID) -> None:
        with self._storage.transaction(write=True) as tx:
            require_student(tx, student_id)
            if tx.evaluations.exists(student_id=student_id):
                raise ConflictError("Перед удалением студента отмените его оценки.")
            tx.students.delete(student_id)
