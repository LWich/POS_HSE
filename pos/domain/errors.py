class AssessmentError(Exception):
    """Операция не выполнена по известной предметной причине"""


class InvalidValueError(AssessmentError):
    """Значение нарушает правило предметной области"""


class NotFoundError(AssessmentError):
    """Запрошенная запись отсутствует"""


class ConflictError(AssessmentError):
    """Операция несовместима с текущим состоянием"""
