"""
Classe de base pour les extracteurs ETL.

Ce module définit l'interface abstraite que tous les extracteurs doivent implémenter.
Les extracteurs sont responsables de lire les données depuis une source (fichier, API, etc.).
"""

from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any

from src.etl.base_component import BaseETLComponent


class BaseExtractor(BaseETLComponent, ABC):
    """
    Classe de base abstraite pour tous les extracteurs.

    Cette classe définit l'interface commune que tous les extracteurs doivent implémenter.
    Les extracteurs sont responsables de lire les données depuis une source externe
    (fichier CSV, API, base de données, etc.) et de les fournir sous forme itérable.
    """

    @abstractmethod
    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Lit les données depuis la source et retourne un itérateur.

        Cette méthode doit être implémentée par les sous-classes pour définir
        comment les données sont extraites de la source spécifique.

        Returns:
            Un itérateur de dictionnaires représentant les lignes de données.
            Chaque dictionnaire contient les données d'une ligne/entrée.

        Raises:
            FileNotFoundError: Si le fichier source n'existe pas
            IOError: Si une erreur de lecture survient
        """
        pass

    def __enter__(self):
        """
        Context manager entry pour gérer les ressources automatiquement.

        Returns:
            L'instance de l'extracteur
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit pour nettoyer les ressources.

        Args:
            exc_type: Type de l'exception si une erreur s'est produite
            exc_val: Valeur de l'exception
            exc_tb: Traceback de l'exception
        """
        pass
