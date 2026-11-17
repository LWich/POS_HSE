from uuid import UUID

from fastapi import APIRouter, Response

from pos.adapters.api.dependencies import ReportsDep
from pos.adapters.api.schemas.analytics import AnalyticsView
from pos.adapters.api.schemas.result import ResultView
from pos.adapters.csv_export import RESULTS_FILENAME, results_csv
from pos.application.analytics import CourseAnalytics
from pos.domain.result import StudentResult

router = APIRouter(tags=["Итоги и аналитика"])


@router.get("/students/{student_id}/result", response_model=ResultView, summary="Итог студента")
def get_result(student_id: UUID, service: ReportsDep) -> StudentResult:
    return service.get_result(student_id)


@router.get("/results", response_model=list[ResultView], summary="Итоги по курсу")
def list_results(service: ReportsDep) -> list[StudentResult]:
    return service.list_results()


@router.get("/analytics", response_model=AnalyticsView, summary="Средние баллы и пропуски")
def analytics(service: ReportsDep) -> CourseAnalytics:
    return service.analytics()


@router.get(
    "/exports/results.csv",
    response_class=Response,
    summary="Скачать итоги в CSV",
    responses={200: {"content": {"text/csv": {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_results(service: ReportsDep) -> Response:
    return Response(
        results_csv(service.list_results()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{RESULTS_FILENAME}"'},
    )
