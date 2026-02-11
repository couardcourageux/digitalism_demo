"""
Pipeline ETL pour Digitalism FastAPI.

Ce package contient tous les modules nécessaires pour le pipeline ETL
(Extract, Transform, Load) permettant d'importer des données depuis
des fichiers CSV vers la base de données.

Nouvelle architecture simplifiée:
- Scripts autonomes pour générer des fichiers JSON à partir des CSV
- Migrations Alembic pour peupler la base de données à partir des JSON
- Composants ETL réutilisables pour les futures extractions (extractors, transformers)

Architecture:
- base_component: Classe de base pour tous les composants ETL
- extractors: Classes pour extraire les données depuis différentes sources
- transformers: Classes pour transformer et nettoyer les données extraites
- utils: Utilitaires et modèles de données intermédiaires
- config: Configuration du pipeline ETL
- scripts: Scripts ETL autonomes (ex: generate_regions_departments_json.py)

Flux actuel pour les régions et départements:
  CSV → ETL (generate_regions_departments_json.py) → JSON → Migration Alembic → BDD
"""

# Configuration
from src.etl.config import (
    CSV_FILE_PATH,
    CSV_ENCODING,
    CSV_DELIMITER,
    CSV_QUOTECHAR,
    CSV_COLUMN_REGION,
    CSV_COLUMN_DEPARTMENT,
    CSV_COLUMN_CODE_DEPARTMENT,
    BATCH_SIZE,
)

# Base Component
from src.etl.base_component import BaseETLComponent

# Extractors
from src.etl.extractors import BaseExtractor, CSVReader

# Transformers
from src.etl.transformers import BaseTransformer, RegionTransformer, DepartmentTransformer

# Utils
from src.etl.utils import (
    get_etl_logger,
    RegionData,
    DepartmentData,
    CityData,
    clean_string,
    validate_csv_row,
    get_csv_value,
    normalize_name,
)

__all__ = [
    # Configuration
    "CSV_FILE_PATH",
    "CSV_ENCODING",
    "CSV_DELIMITER",
    "CSV_QUOTECHAR",
    "CSV_COLUMN_REGION",
    "CSV_COLUMN_DEPARTMENT",
    "CSV_COLUMN_CODE_DEPARTMENT",
    "BATCH_SIZE",
    # Base Component
    "BaseETLComponent",
    # Extractors
    "BaseExtractor",
    "CSVReader",
    # Transformers
    "BaseTransformer",
    "RegionTransformer",
    "DepartmentTransformer",
    # Utils
    "get_etl_logger",
    "RegionData",
    "DepartmentData",
    "CityData",
    "clean_string",
    "validate_csv_row",
    "get_csv_value",
    "normalize_name",
]
