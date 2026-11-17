from collections import defaultdict
from uuid import UUID

from pos.application.analytics import CourseAnalytics, summarize
from pos.application.ports import UnitOfWork
from pos.application.services.students import require_student
from pos.domain.catalog import Rubric, Student
from pos.domain.evaluation import Evaluation
from pos.domain.result import ResultCalculator, StudentResult


class ReportsService:
    def __init__(self, storage: UnitOfWork, results: ResultCalculator) -> None:
        self._storage = storage
        self._results = results

    def get_result(self, student_id: UUID) -> StudentResult:
        with self._storage.transaction() as tx:
            student = require_student(tx, student_id)
            return self._results.calculate(
                student, tx.rubric.get(), tx.evaluations.list(student_id=student_id)
            )

    def list_results(self) -> list[StudentResult]:
        with self._storage.transaction() as tx:
            return self._calculate_results(tx.students.list(), tx.rubric.get(), tx.evaluations.list())

    def analytics(self) -> CourseAnalytics:
        with self._storage.transaction() as tx:
            rubric = tx.rubric.get()
            evaluations = tx.evaluations.list()
            results = self._calculate_results(tx.students.list(), rubric, evaluations)
        return summarize(rubric, results, evaluations)

    def _calculate_results(
        self,
        students: list[Student],
        rubric: Rubric,
        evaluations: list[Evaluation],
    ) -> list[StudentResult]:
        by_student: dict[UUID, list[Evaluation]] = defaultdict(list)
        for evaluation in evaluations:
            by_student[evaluation.student_id].append(evaluation)
        return [self._results.calculate(student, rubric, by_student[student.id]) for student in students]
