from typing import TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from src.model.department import Department


class Region(Base):
    __tablename__ = "regions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    departments: Mapped[list["Department"]] = relationship(back_populates="region")
