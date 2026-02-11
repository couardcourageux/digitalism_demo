"""
Fonctions utilitaires pour le traitement des fichiers CSV.

Ce module fournit des fonctions d'aide pour valider, nettoyer et transformer
les données provenant de fichiers CSV dans le pipeline ETL.
"""

from typing import Dict, Any, Optional


def clean_string(value: Any) -> str:
    """
    Nettoie une valeur de chaîne de caractères.

    Supprime les espaces en trop et retourne une chaîne vide si la valeur est None.

    Args:
        value: La valeur à nettoyer

    Returns:
        La chaîne nettoyée (strip et sans espaces multiples)
    """
    if value is None:
        return ""
    return str(value).strip()


def validate_csv_row(row: Dict[str, Any], required_columns: list[str]) -> bool:
    """
    Valide qu'une ligne CSV contient toutes les colonnes requises.

    Args:
        row: Dictionnaire représentant une ligne CSV
        required_columns: Liste des noms de colonnes requises

    Returns:
        True si toutes les colonnes requises sont présentes, False sinon
    """
    for column in required_columns:
        if column not in row:
            return False
    return True


def get_csv_value(row: Dict[str, Any], key: str, default: Optional[str] = None) -> str:
    """
    Récupère une valeur d'une ligne CSV avec nettoyage automatique.

    Args:
        row: Dictionnaire représentant une ligne CSV
        key: Clé à récupérer
        default: Valeur par défaut si la clé n'existe pas

    Returns:
        La valeur nettoyée ou la valeur par défaut
    """
    value = row.get(key, default)
    return clean_string(value)


def normalize_name(name: str) -> str:
    """
    Normalise un nom en le convertissant en majuscules.

    Cette fonction est utilisée pour normaliser les noms de régions
    et de départements avant leur insertion en base de données.

    Args:
        name: Le nom à normaliser

    Returns:
        Le nom en majuscules, sans espaces en trop
    """
    return clean_string(name).upper()
