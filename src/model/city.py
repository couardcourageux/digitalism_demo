from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from src.model.department import Department


class City(Base):
    __tablename__ = "cities"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id")
    )

    department: Mapped["Department"] = relationship(back_populates="cities")
