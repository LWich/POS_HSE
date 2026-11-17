from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from pos.adapters.sqlite.models.base import Base


class CriterionRow(Base):
    __tablename__ = "criteria"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    name_key: Mapped[str] = mapped_column(Text, unique=True)
    max_score: Mapped[str] = mapped_column(Text)
    weight: Mapped[str] = mapped_column(Text)
