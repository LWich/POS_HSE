import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from pos.adapters.api.router import router
from pos.container import Container
from pos.domain.errors import AssessmentError, ConflictError, InvalidValueError, NotFoundError

ERROR_STATUS = {InvalidValueError: 422, NotFoundError: 404, ConflictError: 409}


def create_app(container: Container | None = None) -> FastAPI:
    graph = container if container is not None else Container()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await run_in_threadpool(graph.initialize)
        yield

    application = FastAPI(
        title="Преподавательская оценка студентов",
        version="1.0.0",
        description="Рубрикатор, выставление оценок, взвешенные итоги и выгрузка по курсу.",
        lifespan=lifespan,
    )
    application.state.container = graph
    application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError) -> Response:
        # Invalid input may itself be impossible to encode as JSON
        details = [
            {"loc": issue["loc"], "msg": issue["msg"], "type": issue["type"]} for issue in error.errors()
        ]
        return Response(
            json.dumps({"detail": details}),
            status_code=422,
            media_type="application/json",
        )

    @application.exception_handler(AssessmentError)
    async def assessment_error(_: Request, error: AssessmentError) -> JSONResponse:
        return JSONResponse({"detail": str(error)}, status_code=ERROR_STATUS[type(error)])

    return application
