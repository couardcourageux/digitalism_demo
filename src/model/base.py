"""
Modèle de base SQLAlchemy pour l'application Digitalism FastAPI.

Ce module définit la classe Base qui sert de classe parente pour tous
les modèles SQLAlchemy du projet. Elle fournit les champs communs
et les méthodes utilitaires partagées.
"""

from sqlalchemy.orm import DeclarativeBase, registry
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.utils.date import get_current_time
from typing import Optional

reg = registry()


class Base(DeclarativeBase):
    """
    Classe de base pour tous les modèles SQLAlchemy.

    Fournit les champs communs : id, created_at, updated_at, deleted_at
    et des méthodes utilitaires pour la gestion des entités.
    """
    registry = reg

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        comment="Identifiant unique auto-incrémenté"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False,
        comment="Date et heure de création de l'entité (UTC)"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_time,
        onupdate=get_current_time,
        nullable=False,
        comment="Date et heure de la dernière mise à jour (UTC)"
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date et heure de la suppression logique (soft delete), NULL si actif"
    )

    def soft_delete(self) -> None:
        """Marque l'entité comme supprimée logiquement."""
        self.deleted_at = get_current_time()

    @property
    def is_deleted(self) -> bool:
        """Indique si l'entité est supprimée logiquement."""
        return self.deleted_at is not None

    def __repr__(self) -> str:
        """Représentation string de l'entité."""
        return f"<{self.__class__.__name__}(id={self.id})>"
