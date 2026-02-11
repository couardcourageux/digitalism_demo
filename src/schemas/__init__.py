"""
Schémas Pydantic pour l'API Digitalism FastAPI.

Ce package contient les schémas de validation pour :
- Base : Schémas de base communs (BaseSchema, TimestampedSchema)
- Region : Schémas pour les régions (Create, Update, Read)
- Department : Schémas pour les départements (Create, Update, Read)
- City : Schémas pour les villes (Create, Update, Read)
- Validators : Validateurs personnalisés

Usage:
    from src.schemas import (
        RegionCreate,
        RegionRead,
        DepartmentCreate,
        DepartmentRead,
        CityCreate,
        CityRead
    )
"""

from .base import BaseSchema, TimestampedSchema
from .validators import (
    uppercase_name,
    uppercase_name_optional,
    validate_region_id,
    validate_region_id_optional,
    validate_postal_code,
    validate_postal_code_optional,
    validate_department_id,
    validate_department_id_optional,
    validate_code_departement,
    validate_code_departement_optional
)
from .region import RegionCreate, RegionUpdate, RegionRead
from .department import DepartmentCreate, DepartmentUpdate, DepartmentRead
from .city import CityCreate, CityUpdate, CityRead

__all__ = [
    # Base schemas
    "BaseSchema",
    "TimestampedSchema",
    # Validators
    "uppercase_name",
    "uppercase_name_optional",
    "validate_region_id",
    "validate_region_id_optional",
    "validate_postal_code",
    "validate_postal_code_optional",
    "validate_department_id",
    "validate_department_id_optional",
    "validate_code_departement",
    "validate_code_departement_optional",
    # Region schemas
    "RegionCreate",
    "RegionUpdate",
    "RegionRead",
    # Department schemas
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentRead",
    # City schemas
    "CityCreate",
    "CityUpdate",
    "CityRead",
]
