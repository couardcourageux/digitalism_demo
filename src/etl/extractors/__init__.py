"""
Extracteurs pour le pipeline ETL.

Ce package contient les classes responsables de l'extraction des données
depuis différentes sources (fichiers CSV, API, bases de données, etc.).
"""

from src.etl.extractors.base_extractor import BaseExtractor
from src.etl.extractors.csv_reader import CSVReader

__all__ = [
    "BaseExtractor",
    "CSVReader",
]
