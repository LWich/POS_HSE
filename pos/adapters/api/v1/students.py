from uuid import UUID

from fastapi import APIRouter

from pos.adapters.api.dependencies import StudentsDep
from pos.adapters.api.schemas.student import StudentInput, StudentView
from pos.domain.catalog import Student

router = APIRouter(prefix="/students", tags=["Студенты"])


@router.get("", response_model=list[StudentView], summary="Список студентов")
def list_students(service: StudentsDep) -> list[Student]:
    return service.list_students()


@router.post("", response_model=StudentView, status_code=201, summary="Добавить студента")
def add_student(body: StudentInput, service: StudentsDep) -> Student:
    return service.add_student(body.name)


@router.get("/{student_id}", response_model=StudentView, summary="Найти студента")
def get_student(student_id: UUID, service: StudentsDep) -> Student:
    return service.get_student(student_id)


@router.put("/{student_id}", response_model=StudentView, summary="Изменить имя студента")
def update_student(student_id: UUID, body: StudentInput, service: StudentsDep) -> Student:
    return service.update_student(student_id, body.name)


@router.delete("/{student_id}", status_code=204, summary="Удалить студента")
def delete_student(student_id: UUID, service: StudentsDep) -> None:
    service.delete_student(student_id)
