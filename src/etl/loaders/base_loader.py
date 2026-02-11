"""
Classe de base pour les loaders ETL.

Ce module définit l'interface abstraite que tous les loaders doivent implémenter.
Les loaders sont responsables de charger les données transformées en base de données.
"""

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

from src.etl.base_component import BaseETLComponent

T = TypeVar("T")


class BaseLoader(BaseETLComponent, ABC, Generic[T]):
    """
    Classe de base abstraite pour tous les loaders.

    Cette classe définit l'interface commune que tous les loaders doivent implémenter.
    Les loaders sont responsables de charger les données transformées depuis le transformer
    vers leur destination finale (base de données, fichier, API, etc.).

    Le type générique T représente le type de données à charger (ex: RegionData, DepartmentData, CityData).
    """

    def __init__(
        self,
        component_name: str,
        entity_name: str = None,
    ):
        """
        Initialise le loader.

        Args:
            component_name: Nom du composant pour le logger
            entity_name: Nom de l'entité traitée (ex: "region", "department", "city")
        """
        super().__init__(component_name=component_name, entity_name=entity_name, component_type="loader")

    @abstractmethod
    def load(self, data: List[T]) -> int:
        """
        Charge les données transformées vers leur destination finale.

        Cette méthode doit être implémentée par les sous-classes pour définir
        comment les données sont chargées (insertion en base de données,
        écriture dans un fichier, envoi vers une API, etc.).

        Args:
            data: Liste des données à charger

        Returns:
            Le nombre d'éléments chargés avec succès

        Raises:
            ValueError: Si les données ne peuvent pas être chargées
            IOError: Si une erreur d'entrée/sortie survient
        """
        pass
