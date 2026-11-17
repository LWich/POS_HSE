import csv
from collections.abc import Iterable
from io import StringIO

from pos.domain.result import StudentResult

RESULTS_FILENAME = "pos-results.csv"


def results_csv(results: Iterable[StudentResult]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(("student_id", "student_name", "total_out_of_10", "graded_count", "criteria_count"))
    for result in results:
        name = result.student_name
        if name.startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠")):
            name = "'" + name
        total = format(result.total, ".2f") if result.total is not None else ""
        writer.writerow((result.student_id, name, total, result.graded_count, result.criteria_count))
    return stream.getvalue().encode("utf-8-sig")
