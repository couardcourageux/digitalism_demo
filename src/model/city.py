"""
Modèle représentant une ville française.
"""

from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Float, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.model.base import Base

if TYPE_CHECKING:
    from src.model.department import Department


class City(Base):
    """
    Représente une ville française.

    Une ville appartient à un département.
    """
    __tablename__ = "cities"
    __table_args__ = (
        CheckConstraint('latitude IS NULL OR (latitude >= -90 AND latitude <= 90)', name='check_latitude_range'),
        CheckConstraint('longitude IS NULL OR (longitude >= -180 AND longitude <= 180)', name='check_longitude_range'),
        CheckConstraint('code_postal IS NOT NULL AND LENGTH(code_postal) = 5', name='check_code_postal_format'),
        UniqueConstraint('name', 'code_postal', name='uq_city_name_code_postal'),
        Index('idx_city_name', 'name'),
        Index('idx_city_department_id', 'department_id'),
        Index('idx_city_code_postal', 'code_postal'),
        Index('ix_city_name', 'name'),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nom de la ville (ex: Paris)"
    )

    code_postal: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        comment="Code postal de la ville (5 chiffres)"
    )

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        index=True,  # Index pour optimiser les jointures
        comment="Identifiant du département parent"
    )

    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="cities"
    )

    # Latitude GPS (optionnel)
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Latitude GPS de la ville"
    )

    # Longitude GPS (optionnel)
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Longitude GPS de la ville"
    )

    @staticmethod
    def calculate_department_from_postal_code(code_postal: str) -> str:
        """
        Calcule le code département à partir du code postal.

        Pour la France métropolitaine, le code département correspond aux 2 premiers chiffres du code postal.
        Pour la Corse (20), il faut distinguer 2A et 2B.
        Pour les DOM-TOM, les codes sont spécifiques (971, 972, 973, 974, 975, 976, 984, 986, 987, 988).

        Args:
            code_postal: Code postal à 5 chiffres

        Returns:
            Code département (2 ou 3 chiffres)

        Raises:
            ValueError: Si le code postal est invalide
        """
        if not code_postal or len(code_postal) != 5 or not code_postal.isdigit():
            raise ValueError(f"Code postal invalide: {code_postal}")

        # Cas spéciaux pour la Corse
        if code_postal.startswith("20"):
            # Départements de Corse: 2A (Corse-du-Sud) et 2B (Haute-Corse)
            # Codes postaux 20000-20199 → 2A
            # Codes postaux 20200-20699 → 2B
            postal_num = int(code_postal)
            if 20000 <= postal_num <= 20199:
                return "2A"
            elif 20200 <= postal_num <= 20699:
                return "2B"
            else:
                return "20"  # Cas par défaut

        # Pour les DOM-TOM, le code département est sur 3 chiffres
        if code_postal.startswith("97") or code_postal.startswith("98"):
            return code_postal[:3]

        # Cas général: les 2 premiers chiffres, sans zéro à gauche
        # Pour les codes département comme "01", on renvoie "1"
        code = code_postal[:2]
        return str(int(code))

    def __repr__(self) -> str:
        return f"<City(id={self.id}, name='{self.name}', department_id={self.department_id})>"
