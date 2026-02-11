"""
Modèle représentant un département français.
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.model.base import Base

if TYPE_CHECKING:
    from src.model.region import Region
    from src.model.city import City


class Department(Base):
    """
    Représente un département français.

    Un département appartient à une région et contient plusieurs villes.
    """
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint('code_departement', name='uq_department_code'),
        Index('idx_department_code', 'code_departement'),
        Index('ix_department_name', 'name'),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nom du département (ex: Paris)"
    )

    # Code département INSEE (2 ou 3 caractères)
    # Exemples: "01", "2A", "75", "971"
    # Pour la France métropolitaine: 2 chiffres (01-95, 2A, 2B)
    # Pour les DOM-TOM: 3 chiffres (971-976, 984, 986-988)
    code_departement: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="Code département INSEE (2 ou 3 caractères)"
    )

    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"),
        index=True,  # Index pour optimiser les jointures
        comment="Identifiant de la région parente"
    )

    region: Mapped["Region"] = relationship(
        "Region",
        back_populates="departments"
    )

    cities: Mapped[list["City"]] = relationship(
        "City",
        back_populates="department",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', region_id={self.region_id})>"
