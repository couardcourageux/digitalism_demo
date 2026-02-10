from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from src.model.region import Region
    from src.model.city import City


class Department(Base):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id")
    )

    region: Mapped["Region"] = relationship(back_populates="departments")

    cities: Mapped[list["City"]] = relationship(back_populates="department")
