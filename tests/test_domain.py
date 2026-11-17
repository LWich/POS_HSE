from datetime import UTC, datetime, timedelta
from decimal import Decimal, Inexact, localcontext
from unittest import TestCase
from uuid import uuid4

from pos.domain.catalog import Criterion, Rubric, Student
from pos.domain.errors import ConflictError, InvalidValueError, NotFoundError
from pos.domain.evaluation import EvaluationFactory
from pos.domain.result import ResultCalculator
from pos.domain.values import Score


class DomainTests(TestCase):
    def setUp(self) -> None:
        self.student = Student(uuid4(), "Анна Волкова")
        self.practice = Criterion(uuid4(), "Практика", Decimal(10), Decimal(40))
        self.project = Criterion(uuid4(), "Проект", Decimal(20), Decimal(60))
        self.rubric = Rubric((self.practice, self.project))
        self.now = datetime(2026, 1, 1, tzinfo=UTC)
        self.factory = EvaluationFactory(lambda: self.now)
        self.calculator = ResultCalculator()

    def test_score_must_be_finite_and_within_criterion(self) -> None:
        for raw_score in ("-0.1", "10.000001", "NaN", "Infinity", "0.0000001"):
            with self.subTest(raw_score=raw_score), self.assertRaises(InvalidValueError):
                self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(raw_score), None)
        for raw_score in ("0", "10", "8.5000000"):
            with self.subTest(raw_score=raw_score):
                grade = self.factory.issue(
                    self.student, self.rubric, self.practice.id, Decimal(raw_score), None
                )
                self.assertEqual(grade.score.value, Decimal(raw_score))

    def test_criterion_must_belong_to_rubric(self) -> None:
        with self.assertRaises(NotFoundError):
            self.factory.issue(self.student, self.rubric, uuid4(), Decimal(1), None)

    def test_rubric_rejects_duplicate_names(self) -> None:
        other = Criterion(uuid4(), "  ПРАКТИКА ", Decimal(1), Decimal(1))
        with self.assertRaises(ConflictError):
            self.rubric.check_criterion_name(other)
        with self.assertRaises(ConflictError):
            Rubric((self.practice, other))
        with self.assertRaises(ConflictError):
            Rubric((self.practice, self.practice))
        self.rubric.check_criterion_name(self.practice)
        self.rubric.check_criterion_name(Criterion(uuid4(), "Экзамен", Decimal(1), Decimal(1)))

    def test_names_are_normalized_and_checked(self) -> None:
        self.assertEqual(Student(uuid4(), "  Анна\tВолкова ").name, "Анна Волкова")
        self.assertEqual(Student(uuid4(), "А" * 120).name, "А" * 120)
        for name in (" ", "А" * 121, "Анна\x00Волкова"):
            with self.subTest(name=name), self.assertRaises(InvalidValueError):
                Student(uuid4(), name)

    def test_score_precision_and_canonical_format(self) -> None:
        at_maximum = Score(Decimal("999999.999999"))
        self.assertEqual(str(at_maximum.value), "999999.999999")
        self.assertEqual(str(Score(Decimal("-0.000")).value), "0")
        self.assertEqual(str(Score(Decimal("8.5000")).value), "8.5")
        with self.assertRaises(InvalidValueError):
            Score(Decimal("1000000"))
        with localcontext() as context:
            context.traps[Inexact] = True
            with self.assertRaises(InvalidValueError):
                Score(Decimal("0.0000001"))

    def test_criterion_requires_positive_maximum_and_weight(self) -> None:
        for maximum, weight in ((0, 1), (1, 0), (1, -1)):
            with self.subTest(maximum=maximum, weight=weight), self.assertRaises(InvalidValueError):
                Criterion(uuid4(), "Экзамен", Decimal(maximum), Decimal(weight))

    def test_correction_preserves_first_evaluation_date(self) -> None:
        grade = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(8), None)
        self.now += timedelta(days=1)

        with self.assertRaises(InvalidValueError):
            self.factory.correct(grade, self.rubric, Decimal(11), None)
        corrected = self.factory.correct(grade, self.rubric, Decimal(9), "  Перепроверено  ")
        self.assertEqual(corrected.evaluated_at, grade.evaluated_at)
        self.assertEqual(corrected.updated_at, self.now)
        self.assertEqual(corrected.score.value, Decimal(9))
        self.assertEqual(corrected.comment, "Перепроверено")

    def test_issued_evaluation_preserves_identity_and_comment(self) -> None:
        comment = "А" * 1000
        grade = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(8), comment)
        self.assertEqual(grade.student_id, self.student.id)
        self.assertEqual(grade.criterion_id, self.practice.id)
        self.assertEqual(grade.evaluated_at, self.now)
        self.assertEqual(grade.updated_at, self.now)
        self.assertEqual(grade.comment, comment)
        with self.assertRaisesRegex(InvalidValueError, "1000"):
            self.factory.correct(grade, self.rubric, Decimal(8), comment + "А")
        corrected = self.factory.correct(grade, self.rubric, Decimal(8), " \n ")
        self.assertIsNone(corrected.comment)

    def test_total_normalizes_scores_and_weights(self) -> None:
        practice = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(8), None)
        project = self.factory.issue(self.student, self.rubric, self.project.id, Decimal(15), None)
        result = self.calculator.calculate(self.student, self.rubric, (practice, project))
        self.assertEqual(result.student_id, self.student.id)
        self.assertEqual(result.student_name, self.student.name)
        self.assertEqual(result.criteria_count, 2)
        self.assertEqual(result.total, Decimal("7.70"))
        self.assertEqual(result.missing_criterion_ids, ())

    def test_total_keeps_hundredths_under_low_decimal_precision(self) -> None:
        practice = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(8), None)
        project = self.factory.issue(self.student, self.rubric, self.project.id, Decimal("14.9"), None)
        with localcontext(prec=2) as context:
            context.traps[Inexact] = True
            result = self.calculator.calculate(self.student, self.rubric, (practice, project))
        self.assertEqual(result.total, Decimal("7.67"))

    def test_other_students_scores_are_excluded(self) -> None:
        other = Student(uuid4(), "Иван")
        practice = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(8), None)
        project = self.factory.issue(other, self.rubric, self.project.id, Decimal(20), None)
        result = self.calculator.calculate(self.student, self.rubric, (practice, project))
        self.assertEqual(result.total, Decimal("3.20"))
        self.assertEqual(result.missing_criterion_ids, (self.project.id,))

    def test_missing_and_explicit_zero_are_distinguished(self) -> None:
        zero = self.factory.issue(self.student, self.rubric, self.practice.id, Decimal(0), None)
        result = self.calculator.calculate(self.student, self.rubric, (zero,))
        self.assertEqual(result.total, Decimal("0.00"))
        self.assertEqual(result.graded_count, 1)
        self.assertEqual(result.missing_criterion_ids, (self.project.id,))
        self.assertIsNone(self.calculator.calculate(self.student, Rubric(()), ()).total)

    def test_result_rounds_half_up_once(self) -> None:
        criterion = Criterion(uuid4(), "Экзамен", Decimal(2000), Decimal(1))
        rubric = Rubric((criterion,))
        grade = self.factory.issue(self.student, rubric, criterion.id, Decimal(201), None)
        self.assertEqual(
            self.calculator.calculate(self.student, rubric, (grade,)).total, Decimal("1.01")
        )
