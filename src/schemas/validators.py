"""Validateurs partagés pour les schémas Pydantic."""

import re


def uppercase_name(v: str) -> str:
    """Convertit le nom en majuscules."""
    if not v or not v.strip():
        raise ValueError('Le nom ne peut pas être vide')
    return v.strip().upper()


def uppercase_name_optional(v: str | None) -> str | None:
    """Convertit le nom en majuscules si présent."""
    if v is not None:
        if not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip().upper()
    return v


def validate_region_id(v: int) -> int:
    """Valide que l'ID de région est positif."""
    if v <= 0:
        raise ValueError("L'ID de région doit être positif")
    return v


def validate_region_id_optional(v: int | None) -> int | None:
    """Valide que l'ID de région est positif si présent."""
    if v is not None and v <= 0:
        raise ValueError("L'ID de région doit être positif")
    return v


def validate_postal_code(v: str) -> str:
    """Valide que le code postal est composé de 5 chiffres."""
    if not v or not v.strip():
        raise ValueError('Le code postal ne peut pas être vide')
    code = v.strip()
    if len(code) != 5 or not code.isdigit():
        raise ValueError('Le code postal doit être composé de 5 chiffres')
    return code


def validate_postal_code_optional(v: str | None) -> str | None:
    """Valide que le code postal est composé de 5 chiffres si présent."""
    if v is not None:
        return validate_postal_code(v)
    return v


def validate_department_id(v: int) -> int:
    """Valide que l'ID de département est positif."""
    if v <= 0:
        raise ValueError("L'ID de département doit être positif")
    return v


def validate_department_id_optional(v: int | None) -> int | None:
    """Valide que l'ID de département est positif si présent."""
    if v is not None and v <= 0:
        raise ValueError("L'ID de département doit être positif")
    return v


def validate_code_departement(v: str) -> str:
    """Valide le code département français (1-3 chiffres ou 2A/2B pour la Corse)."""
    if not v or not v.strip():
        raise ValueError('Le code département ne peut pas être vide')
    code = v.strip().upper()
    # Pattern: 1-3 chiffres (ex: 1, 01, 75, 971) OU 2A/2B pour la Corse
    pattern = r'^[0-9]{1,3}$|^2[AB]$'
    if not re.match(pattern, code):
        raise ValueError(
            'Le code département doit être composé de 1-3 chiffres '
            'ou être 2A/2B pour la Corse'
        )
    return code


def validate_code_departement_optional(v: str | None) -> str | None:
    """Valide le code département français si présent."""
    if v is not None:
        return validate_code_departement(v)
    return v
