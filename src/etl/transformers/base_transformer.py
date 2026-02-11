"""
Classe de base pour les transformers ETL.

Ce module définit l'interface abstraite que tous les transformers doivent implémenter.
Les transformers sont responsables de transformer et nettoyer les données extraites
avant leur chargement en base de données.
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, TypeVar, Generic, Optional

from src.etl.base_component import BaseETLComponent

T = TypeVar("T")


class BaseTransformer(BaseETLComponent, ABC, Generic[T]):
    """
    Classe de base abstraite pour tous les transformers.

    Cette classe définit l'interface commune que tous les transformers doivent implémenter.
    Les transformers sont responsables de transformer et nettoyer les données extraites
    depuis une source (fichier CSV, API, etc.) en structures de données adaptées
    pour leur chargement en base de données.

    Le type générique T représente le type de données transformées produites
    par le transformer (ex: RegionData, DepartmentData).
    """

    def __init__(
        self,
        component_name: str,
        entity_name: Optional[str] = None,
    ):
        """
        Initialise le transformer.

        Args:
            component_name: Nom du composant pour le logger
            entity_name: Nom de l'entité traitée (ex: "region", "department")
        """
        super().__init__(component_name=component_name, entity_name=entity_name, component_type="transformer")

    @abstractmethod
    def transform(self, data: Iterator[Dict[str, Any]]) -> list[T]:
        """
        Transforme les données extraites en structures de données adaptées.

        Cette méthode doit être implémentée par les sous-classes pour définir
        comment les données sont transformées depuis leur format brut
        (dictionnaires provenant de l'extracteur) vers le format souhaité
        pour le chargement.

        Args:
            data: Un itérateur de dictionnaires représentant les données brutes

        Returns:
            Une liste de données transformées (type T)

        Raises:
            ValueError: Si les données ne peuvent pas être transformées
        """
        pass

    def _validate_result_not_empty(self, result: list[T]) -> None:
        """
        Valide que le résultat de la transformation n'est pas vide.

        Args:
            result: Résultat de la transformation

        Raises:
            ValueError: Si le résultat est vide
        """
        if not result:
            error_msg = f"Aucun{'' if self._entity_name and self._entity_name.endswith('e') else 'e'} {self._entity_name or 'donnée'} trouvé(e) dans les données"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def _log_transformed_items(self, items: list[T], format_func: Optional[callable] = None) -> None:
        """
        Log les éléments transformés.

        Args:
            items: Liste des éléments transformés
            format_func: Fonction optionnelle pour formater chaque élément
        """
        self.logger.info(f"{len(items)} {self._entity_name or 'élément'}(s) unique(s) trouvé(s)")
        for item in items:
            if format_func:
                self.logger.debug(f"  - {format_func(item)}")
            else:
                self.logger.debug(f"  - {item}")
