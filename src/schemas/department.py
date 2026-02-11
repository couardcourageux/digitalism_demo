from pydantic import field_validator
from .base import BaseSchema, TimestampedSchema
from .validators import (
    uppercase_name,
    uppercase_name_optional,
    validate_region_id,
    validate_region_id_optional,
    validate_code_departement,
    validate_code_departement_optional
)


class DepartmentCreate(BaseSchema):
    """Schéma de création pour Department"""
    name: str
    code_departement: str
    region_id: int

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: str) -> str:
        """Convertit le nom en majuscules"""
        return uppercase_name(v)

    @field_validator('code_departement')
    @classmethod
    def validate_code_departement(cls, v: str) -> str:
        """Valide le code département français (2-3 chiffres ou 2A/2B pour la Corse)"""
        return validate_code_departement(v)

    @field_validator('region_id')
    @classmethod
    def validate_region_id(cls, v: int) -> int:
        """Valide que l'ID de région est positif"""
        return validate_region_id(v)


class DepartmentUpdate(BaseSchema):
    """Schéma de mise à jour pour Department"""
    name: str | None = None
    code_departement: str | None = None
    region_id: int | None = None

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: str | None) -> str | None:
        """Convertit le nom en majuscules si présent"""
        return uppercase_name_optional(v)

    @field_validator('code_departement')
    @classmethod
    def validate_code_departement(cls, v: str | None) -> str | None:
        """Valide le code département français si présent"""
        return validate_code_departement_optional(v)

    @field_validator('region_id')
    @classmethod
    def validate_region_id(cls, v: int | None) -> int | None:
        """Valide que l'ID de région est positif si présent"""
        return validate_region_id_optional(v)


class DepartmentRead(TimestampedSchema):
    """Schéma de lecture pour Department"""
    name: str
    code_departement: str
    region_id: int
