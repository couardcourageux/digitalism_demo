from pydantic import field_validator
from .base import BaseSchema, TimestampedSchema
from .validators import uppercase_name, uppercase_name_optional


class RegionCreate(BaseSchema):
    """Schéma de création pour Region"""
    name: str

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: str) -> str:
        """Convertit le nom en majuscules"""
        return uppercase_name(v)


class RegionUpdate(BaseSchema):
    """Schéma de mise à jour pour Region"""
    name: str | None = None

    @field_validator('name')
    @classmethod
    def uppercase_name(cls, v: str | None) -> str | None:
        """Convertit le nom en majuscules si présent"""
        return uppercase_name_optional(v)


class RegionRead(TimestampedSchema):
    """Schéma de lecture pour Region"""
    name: str
