"""
Package pour les loaders ETL.

Ce package contient les loaders responsables de charger les données
transformées en base de données.
"""

from src.etl.loaders.base_loader import BaseLoader
from src.etl.loaders.city_loader import CityLoader

__all__ = ["BaseLoader", "CityLoader"]
