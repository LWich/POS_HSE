from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from pos.domain.errors import ConflictError, InvalidValueError, NotFoundError
from pos.domain.values import Score, clean_name, numeric_value


@dataclass(frozen=True, slots=True)
class Student:
    id: UUID
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", clean_name(self.name, "Имя студента"))


@dataclass(frozen=True, slots=True)
class Criterion:
    id: UUID
    name: str
    max_score: Decimal
    weight: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", clean_name(self.name, "Название критерия"))
        max_score = numeric_value(self.max_score, "Максимальное значение балла")
        weight = numeric_value(self.weight, "Значение веса")
        if max_score <= 0 or weight <= 0:
            raise InvalidValueError("Максимальный балл и вес должны быть больше нуля.")
        object.__setattr__(self, "max_score", max_score)
        object.__setattr__(self, "weight", weight)

    @property
    def name_key(self) -> str:
        return self.name.casefold()

    def accepts_score(self, score: Score) -> bool:
        return score.value <= self.max_score

    def check_score(self, score: Score) -> None:
        if not self.accepts_score(score):
            raise InvalidValueError(
                f"Балл по критерию «{self.name}» должен быть от 0 до {self.max_score:f}."
            )


@dataclass(frozen=True, slots=True)
class Rubric:
    criteria: tuple[Criterion, ...]

    def __post_init__(self) -> None:
        if len({item.id for item in self.criteria}) != len(self.criteria):
            raise ConflictError("В рубрикаторе повторяется идентификатор критерия.")
        if len({item.name_key for item in self.criteria}) != len(self.criteria):
            raise ConflictError("Критерий с таким названием уже есть в рубрикаторе.")

    def require(self, criterion_id: UUID) -> Criterion:
        for criterion in self.criteria:
            if criterion.id == criterion_id:
                return criterion
        raise NotFoundError(f"Критерий {criterion_id} отсутствует в рубрикаторе.")

    def check_criterion_name(self, criterion: Criterion) -> None:
        if any(
            item.id != criterion.id and item.name_key == criterion.name_key for item in self.criteria
        ):
            raise ConflictError("Критерий с таким названием уже есть в рубрикаторе.")
