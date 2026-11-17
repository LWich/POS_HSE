from dataclasses import dataclass
from decimal import Context, Decimal

from pos.domain.errors import InvalidValueError


def clean_name(value: str, label: str) -> str:
    value = " ".join(value.split())
    if not value or len(value) > 120 or any(not char.isprintable() for char in value):
        raise InvalidValueError(f"{label} должно содержать от 1 до 120 печатных символов.")
    return value


def numeric_value(value: Decimal, label: str) -> Decimal:
    if not value.is_finite() or not 0 <= value <= Decimal("999999.999999"):
        raise InvalidValueError(f"Для поля «{label}» допустимы числа от 0 до 999999.999999.")
    exact = value.quantize(Decimal("0.000001"), context=Context(prec=16))
    if exact != value:
        raise InvalidValueError(f"Для поля «{label}» допустимо до 6 знаков после запятой.")
    if not exact:
        return Decimal(0)
    return Decimal(format(exact, "f").rstrip("0").rstrip("."))


@dataclass(frozen=True, slots=True)
class Score:
    value: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", numeric_value(self.value, "Балл"))
