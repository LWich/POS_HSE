from concurrent.futures import ThreadPoolExecutor
from csv import DictReader
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx2 import Response

from pos.adapters.api.app import create_app
from pos.container import Container


class ApiTests(TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        self.database = Path(directory) / "test.sqlite3"
        self.client = self.enterContext(TestClient(create_app(Container(self.database))))

    def student(self, name: str = "Анна Волкова") -> str:
        response = self.client.post("/students", json={"name": name})
        self.assertEqual(response.status_code, 201, response.text)
        student_id = response.json()["id"]
        assert isinstance(student_id, str)
        return student_id

    def criterion(self, name: str = "Практика", maximum: int = 10, weight: int = 40) -> str:
        response = self.client.post(
            "/criteria", json={"name": name, "max_score": maximum, "weight": weight}
        )
        self.assertEqual(response.status_code, 201, response.text)
        criterion_id = response.json()["id"]
        assert isinstance(criterion_id, str)
        return criterion_id

    def issue(self, student_id: str, criterion_id: str, score: str | int) -> Response:
        return self.client.post(
            f"/students/{student_id}/evaluations",
            json={"criterion_id": criterion_id, "score": score},
        )

    def test_catalog_crud(self) -> None:
        self.assertEqual(self.client.get("/students").json(), [])
        self.assertEqual(self.client.post("/students", json={"name": " "}).status_code, 422)
        student = self.student()
        criterion = self.criterion()
        self.assertEqual(self.client.get(f"/students/{student}").json()["name"], "Анна Волкова")
        self.assertEqual(self.client.get(f"/criteria/{criterion}").json()["max_score"], "10")
        response = self.client.put(f"/students/{student}", json={"name": "Анна Орлова"})
        self.assertEqual(response.json()["name"], "Анна Орлова")
        response = self.client.post(
            "/criteria", json={"name": "ПРАКТИКА", "max_score": 10, "weight": 20}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.delete(f"/criteria/{criterion}").status_code, 204)
        self.assertEqual(self.client.get(f"/criteria/{criterion}").status_code, 404)
        self.assertEqual(self.client.delete(f"/students/{student}").status_code, 204)
        self.assertEqual(self.client.get("/students").json(), [])

    def test_non_finite_input_returns_validation_errors(self) -> None:
        for value in ("NaN", "Infinity", "-Infinity", '"NaN"', "1e400"):
            with self.subTest(value=value):
                response = self.client.post(
                    "/criteria",
                    content='{"name":"Практика","max_score":10,"weight":' + value + "}",
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(response.json()["detail"][0]["loc"], ["body", "weight"])
        self.assertEqual(self.client.get("/criteria").json(), [])

    def test_service_routes(self) -> None:
        self.assertEqual(self.client.get("/", follow_redirects=False).headers["location"], "/docs")
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})

    def test_json_numbers_and_strings_preserve_score_precision(self) -> None:
        student = self.student()
        criterion = self.criterion()
        grades = f"/students/{student}/evaluations"
        grade = f"{grades}/{criterion}"
        headers = {"Content-Type": "application/json"}
        for value in ("10.0000000000000001", "8.1234560000000001"):
            for token in (value, f'"{value}"'):
                with self.subTest(token=token):
                    body = f'{{"criterion_id":"{criterion}","score":{token}}}'
                    self.assertEqual(
                        self.client.post(grades, content=body, headers=headers).status_code, 422
                    )

        valid = '{"criterion_id":"' + criterion + '","score":8.123456}'
        issued = self.client.post(grades, content=valid, headers=headers)
        self.assertEqual(issued.status_code, 201, issued.text)
        self.assertEqual(issued.json()["score"], "8.123456")
        for token in ("10.0000000000000001", '"10.0000000000000001"'):
            with self.subTest(correction=token):
                body = f'{{"score":{token}}}'
                self.assertEqual(self.client.put(grade, content=body, headers=headers).status_code, 422)
        self.assertEqual(self.client.get(grade).json()["score"], "8.123456")

    def test_json_numbers_preserve_criterion_precision(self) -> None:
        headers = {"Content-Type": "application/json"}
        for maximum, weight in (("10.0000000000000001", "40"), ("10", "40.0000000000000001")):
            with self.subTest(maximum=maximum, weight=weight):
                body = f'{{"name":"Практика","max_score":{maximum},"weight":{weight}}}'
                self.assertEqual(
                    self.client.post("/criteria", content=body, headers=headers).status_code, 422
                )
        self.assertEqual(self.client.get("/criteria").json(), [])

    def test_grade_lifecycle_updates_results(self) -> None:
        student = self.student()
        criterion = self.criterion()
        grades = f"/students/{student}/evaluations"
        grade = f"{grades}/{criterion}"
        result = f"/students/{student}/result"
        self.assertEqual(self.issue(student, str(uuid4()), 4).status_code, 404)
        self.assertEqual(self.issue(str(uuid4()), criterion, 4).status_code, 404)
        self.assertEqual(self.client.put(grade, json={"score": 4}).status_code, 404)
        self.assertEqual(self.issue(student, criterion, 12).status_code, 422)
        self.assertEqual(self.client.get(grades).json(), [])

        issued = self.issue(student, criterion, "8.5")
        self.assertEqual(issued.status_code, 201, issued.text)
        self.assertEqual(self.issue(student, criterion, 6).status_code, 409)
        self.assertEqual(self.client.get(result).json()["total"], "8.50")
        self.assertEqual(self.client.put(grade, json={"score": -1}).status_code, 422)
        self.assertEqual(self.client.get(grade).json()["score"], "8.5")

        corrected = self.client.put(grade, json={"score": 7, "comment": "Уточнение"})
        self.assertEqual(corrected.status_code, 200, corrected.text)
        self.assertEqual(corrected.json()["evaluated_at"], issued.json()["evaluated_at"])
        self.assertEqual(self.client.get(grades).json()[0]["comment"], "Уточнение")
        self.assertEqual(self.client.get(result).json()["total"], "7.00")
        self.assertEqual(self.client.delete(grade).status_code, 204)
        self.assertEqual(self.client.delete(grade).status_code, 404)
        self.assertEqual(self.client.get(result).json()["missing_criterion_ids"], [criterion])
        self.assertEqual(self.client.get(result).json()["total"], "0.00")

    def test_rubric_changes_preserve_existing_evaluations(self) -> None:
        student = self.student()
        practice = self.criterion()
        project = self.criterion("Проект", 20, 60)
        self.assertEqual(self.issue(student, practice, 8).status_code, 201)
        self.assertEqual(self.issue(student, project, 15).status_code, 201)
        path = f"/criteria/{practice}"
        result = f"/students/{student}/result"

        self.assertEqual(self.client.delete(path).status_code, 409)
        self.assertEqual(self.client.delete(f"/students/{student}").status_code, 409)
        invalid = self.client.put(path, json={"name": "Практика", "max_score": 7, "weight": 60})
        self.assertEqual(invalid.status_code, 409)
        self.assertEqual(self.client.get(path).json()["weight"], "40")
        self.assertEqual(self.client.get(result).json()["total"], "7.70")

        response = self.client.put(path, json={"name": "Практика", "max_score": 10, "weight": 60})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get(result).json()["total"], "7.75")

        self.assertEqual(
            self.client.put(path, json={"name": "Практика", "max_score": 12, "weight": 60}).status_code,
            200,
        )
        corrected = self.client.put(f"/students/{student}/evaluations/{practice}", json={"score": 11})
        self.assertEqual(corrected.status_code, 200, corrected.text)
        self.assertEqual(corrected.json()["score"], "11")

    def test_csv_and_analytics_report_current_results(self) -> None:
        anna = self.student()
        ivan = self.student("Иван Ким")
        self.assertIsNone(self.client.get(f"/students/{anna}/result").json()["total"])
        practice = self.criterion()
        project = self.criterion("Проект", 20, 60)
        self.assertEqual(self.issue(anna, practice, 8).status_code, 201)
        self.assertEqual(self.issue(anna, project, 15).status_code, 201)
        self.assertEqual(self.issue(ivan, practice, 10).status_code, 201)

        results = {item["student_id"]: item["total"] for item in self.client.get("/results").json()}
        self.assertEqual(results, {anna: "7.70", ivan: "4.00"})
        report = self.client.get("/analytics").json()
        self.assertEqual(report["average_total"], "5.85")
        self.assertEqual(report["graded_count"], 3)
        by_name = {criterion["name"]: criterion for criterion in report["criteria"]}
        self.assertEqual(by_name["Практика"]["average_score"], "9.00")
        self.assertEqual(by_name["Проект"]["missing_count"], 1)

        response = self.client.get("/exports/results.csv")
        self.assertEqual(
            response.headers["content-disposition"], 'attachment; filename="pos-results.csv"'
        )
        rows = list(DictReader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(
            {row["student_name"]: row["total_out_of_10"] for row in rows},
            {"Анна Волкова": "7.70", "Иван Ким": "4.00"},
        )

    def test_parallel_issuance_has_one_winner(self) -> None:
        student = self.student()
        criterion = self.criterion()
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(lambda score: self.issue(student, criterion, score), (4, 8)))
        self.assertEqual(sorted(response.status_code for response in responses), [201, 409])
        self.assertEqual(len(self.client.get(f"/students/{student}/evaluations").json()), 1)

    def test_restart_reads_stored_data(self) -> None:
        student = self.student()
        criterion = self.criterion()
        self.assertEqual(self.issue(student, criterion, 8).status_code, 201)
        with TestClient(create_app(Container(self.database))) as other:
            self.assertEqual(other.get(f"/students/{student}/result").json()["total"], "8.00")
