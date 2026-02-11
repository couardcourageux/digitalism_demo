"""
Dépendances FastAPI pour l'injection des repositories.

Ce module définit des fonctions de dépendance qui permettent d'injecter
directement les repositories dans les routeurs, évitant ainsi la répétition
du pattern d'instanciation dans chaque fonction de routeur.
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated

from src.database import get_db
from src.repository.city import CityRepository
from src.repository.department import DepartmentRepository
from src.repository.region import RegionRepository


def get_city_repository(db: Session = Depends(get_db)) -> CityRepository:
    """
    Dépendance pour injecter un CityRepository.

    Args:
        db: Session de base de données (injectée par get_db)

    Returns:
        Une instance de CityRepository
    """
    return CityRepository(db)


def get_department_repository(db: Session = Depends(get_db)) -> DepartmentRepository:
    """
    Dépendance pour injecter un DepartmentRepository.

    Args:
        db: Session de base de données (injectée par get_db)

    Returns:
        Une instance de DepartmentRepository
    """
    return DepartmentRepository(db)


def get_region_repository(db: Session = Depends(get_db)) -> RegionRepository:
    """
    Dépendance pour injecter un RegionRepository.

    Args:
        db: Session de base de données (injectée par get_db)

    Returns:
        Une instance de RegionRepository
    """
    return RegionRepository(db)


# Alias de type pour l'injection de dépendances FastAPI
CityRepoDep = Annotated[CityRepository, Depends(get_city_repository)]
DepartmentRepoDep = Annotated[DepartmentRepository, Depends(get_department_repository)]
RegionRepoDep = Annotated[RegionRepository, Depends(get_region_repository)]
