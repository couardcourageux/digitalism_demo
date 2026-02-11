"""Repositories pour l'application."""

from .base import BaseRepository
from .region import RegionRepository
from .department import DepartmentRepository
from .city import CityRepository

__all__ = [
    "BaseRepository",
    "RegionRepository",
    "DepartmentRepository",
    "CityRepository",
]
