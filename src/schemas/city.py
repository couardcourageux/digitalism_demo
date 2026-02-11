"""Schémas Pydantic pour City."""

from pydantic import field_validator
from typing import Optional
from .base import BaseSchema, TimestampedSchema
from .validators import (
    uppercase_name,
    uppercase_name_optional,
    validate_postal_code,
    validate_postal_code_optional
)


class CityCreate(BaseSchema):
    """Schéma de création pour City"""
    name: str
    code_postal: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: str) -> str:
        """Convertit le nom en majuscules"""
        return uppercase_name(v)

    @field_validator('code_postal')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Valide que le code postal est composé de 5 chiffres"""
        return validate_postal_code(v)


class CityUpdate(BaseSchema):
    """Schéma de mise à jour pour City"""
    name: Optional[str] = None
    code_postal: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: Optional[str]) -> Optional[str]:
        """Convertit le nom en majuscules si présent"""
        return uppercase_name_optional(v)

    @field_validator('code_postal')
    @classmethod
    def validate_postal_code(cls, v: Optional[str]) -> Optional[str]:
        """Valide que le code postal est composé de 5 chiffres si présent"""
        return validate_postal_code_optional(v)


class CityRead(TimestampedSchema):
    """Schéma de lecture pour City"""
    name: str
    code_postal: str
    department_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
