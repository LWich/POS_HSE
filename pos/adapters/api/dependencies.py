from typing import Annotated

from fastapi import Depends, Request

from pos.application.services.criteria import CriteriaService
from pos.application.services.evaluations import EvaluationsService
from pos.application.services.reports import ReportsService
from pos.application.services.students import StudentsService
from pos.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_students(container: ContainerDep) -> StudentsService:
    return container.students


def get_criteria(container: ContainerDep) -> CriteriaService:
    return container.criteria


def get_evaluations(container: ContainerDep) -> EvaluationsService:
    return container.evaluations


def get_reports(container: ContainerDep) -> ReportsService:
    return container.reports


StudentsDep = Annotated[StudentsService, Depends(get_students)]
CriteriaDep = Annotated[CriteriaService, Depends(get_criteria)]
EvaluationsDep = Annotated[EvaluationsService, Depends(get_evaluations)]
ReportsDep = Annotated[ReportsService, Depends(get_reports)]
