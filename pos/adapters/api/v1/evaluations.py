from uuid import UUID

from fastapi import APIRouter

from pos.adapters.api.decimal_route import DecimalRoute
from pos.adapters.api.dependencies import EvaluationsDep
from pos.adapters.api.schemas.evaluation import EvaluationInput, EvaluationView, ScoreInput

router = APIRouter(
    prefix="/students/{student_id}/evaluations", tags=["Оценки"], route_class=DecimalRoute
)


@router.get("", summary="Список оценок студента")
def list_evaluations(student_id: UUID, service: EvaluationsDep) -> list[EvaluationView]:
    return [EvaluationView.from_evaluation(item) for item in service.list_evaluations(student_id)]


@router.post("", status_code=201, summary="Выставить оценку")
def issue_evaluation(student_id: UUID, body: EvaluationInput, service: EvaluationsDep) -> EvaluationView:
    evaluation = service.issue_evaluation(student_id, body.criterion_id, body.score, body.comment)
    return EvaluationView.from_evaluation(evaluation)


@router.get("/{criterion_id}", summary="Показать оценку")
def get_evaluation(student_id: UUID, criterion_id: UUID, service: EvaluationsDep) -> EvaluationView:
    return EvaluationView.from_evaluation(service.get_evaluation(student_id, criterion_id))


@router.put("/{criterion_id}", summary="Исправить оценку")
def correct_evaluation(
    student_id: UUID,
    criterion_id: UUID,
    body: ScoreInput,
    service: EvaluationsDep,
) -> EvaluationView:
    evaluation = service.correct_evaluation(student_id, criterion_id, body.score, body.comment)
    return EvaluationView.from_evaluation(evaluation)


@router.delete("/{criterion_id}", status_code=204, summary="Отменить оценку")
def cancel_evaluation(student_id: UUID, criterion_id: UUID, service: EvaluationsDep) -> None:
    service.cancel_evaluation(student_id, criterion_id)
