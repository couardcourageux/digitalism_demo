"""
Modèle représentant une région administrative française.
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.model.base import Base

if TYPE_CHECKING:
    from src.model.department import Department


class Region(Base):
    """
    Représente une région administrative française.

    Une région contient plusieurs départements.
    """
    __tablename__ = "regions"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nom de la région (ex: Île-de-France)"
    )

    # Index pour optimiser les recherches par nom
    __table_args__ = (
        Index('ix_region_name', 'name'),
    )

    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="region",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, name='{self.name}')>"
