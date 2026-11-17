from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from pos.adapters.sqlite.models.base import Base


class StudentRow(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
