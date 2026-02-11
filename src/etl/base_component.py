"""
Classe de base pour tous les composants ETL.

Ce module définit une classe de base commune pour tous les composants ETL
(extractors, transformers, loaders) afin d'éliminer les duplications de code
liées au logging et à la configuration.
"""

import logging
from typing import Optional

from src.etl.utils.logger import get_etl_logger


class BaseETLComponent:
    """
    Classe de base pour tous les composants ETL.

    Cette classe fournit des fonctionnalités communes à tous les composants ETL:
    - Initialisation automatique du logger
    - Méthodes de logging standardisées
    - Attributs pour l'identification du composant

    Attributes:
        logger: Logger configuré pour le composant
        _entity_name: Nom de l'entité traitée par le composant (ex: "region", "department")
        _component_type: Type du composant (ex: "extractor", "transformer", "loader")
    """

    def __init__(
        self,
        component_name: str,
        entity_name: Optional[str] = None,
        component_type: Optional[str] = None,
    ):
        """
        Initialise le composant ETL.

        Args:
            component_name: Nom du composant pour le logger (ex: "csv_reader", "region_transformer")
            entity_name: Nom de l'entité traitée (ex: "region", "department")
            component_type: Type du composant (ex: "extractor", "transformer", "loader")
        """
        self.logger = get_etl_logger(component_name)
        self._entity_name = entity_name
        self._component_type = component_type

    def _log_start(self, message: Optional[str] = None) -> None:
        """
        Log le début d'une opération.

        Args:
            message: Message personnalisé (optionnel)
        """
        if message:
            self.logger.info(message)
        elif self._entity_name and self._component_type:
            self.logger.info(
                f"Début de l'opération {self._component_type} sur {self._entity_name}"
            )
        else:
            self.logger.info("Début de l'opération")

    def _log_success(self, count: int, message: Optional[str] = None) -> None:
        """
        Log le succès d'une opération.

        Args:
            count: Nombre d'éléments traités
            message: Message personnalisé (optionnel)
        """
        if message:
            # Message personnalisé fourni, l'utiliser tel quel
            self.logger.info(message)
        elif self._entity_name:
            # Utiliser le nom de l'entité pour un message plus spécifique
            self.logger.info(f"{count} {self._entity_name}(s) traité(s) avec succès")
        else:
            # Fallback: message générique sans nom d'entité
            self.logger.info(f"{count} élément(s) traité(s) avec succès")

    def _log_error(self, error: Exception, message: Optional[str] = None) -> None:
        """
        Log une erreur survenue lors d'une opération.

        Args:
            error: Exception survenue
            message: Message personnalisé (optionnel)
        """
        if message:
            self.logger.error(f"{message}: {error}")
        else:
            self.logger.error(f"Erreur: {error}")

    def _log_debug(self, message: str) -> None:
        """
        Log un message de debug.

        Args:
            message: Message à logger
        """
        self.logger.debug(message)
