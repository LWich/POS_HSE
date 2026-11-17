from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pos.adapters.sqlite.storage import SQLiteUnitOfWork
from pos.application.services.criteria import CriteriaService
from pos.application.services.evaluations import EvaluationsService
from pos.application.services.reports import ReportsService
from pos.application.services.students import StudentsService
from pos.domain.evaluation import EvaluationFactory
from pos.domain.result import ResultCalculator
from pos.settings import Settings


def utc_now() -> datetime:
    return datetime.now(UTC)


class Container:
    """Контейнер DI и точка сборки общего графа зависимостей"""

    def __init__(
        self,
        database_path: Path | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        settings = Settings()
        path = database_path if database_path is not None else settings.db_path
        self.storage = SQLiteUnitOfWork(path, timeout=settings.db_timeout)
        self.students = StudentsService(self.storage)
        self.criteria = CriteriaService(self.storage)
        self.evaluations = EvaluationsService(self.storage, EvaluationFactory(clock))
        self.reports = ReportsService(self.storage, ResultCalculator())

    def initialize(self) -> None:
        self.storage.initialize()
