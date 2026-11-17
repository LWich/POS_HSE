from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from pos.adapters.sqlite.models.base import Base


class EvaluationRow(Base):
    __tablename__ = "evaluations"
    __table_args__ = (Index("evaluations_criterion", "criterion_id"),)

    student_id: Mapped[str] = mapped_column(
        Text, ForeignKey("students.id", ondelete="RESTRICT"), primary_key=True
    )
    criterion_id: Mapped[str] = mapped_column(
        Text, ForeignKey("criteria.id", ondelete="RESTRICT"), primary_key=True
    )
    score: Mapped[str] = mapped_column(Text)
    evaluated_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
