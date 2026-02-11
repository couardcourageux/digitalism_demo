"""
Configuration pour les modules ETL.

Ce module contient toutes les configurations nécessaires pour le pipeline ETL,
y compris les chemins des fichiers, l'encodage et les paramètres de traitement.
"""

from pathlib import Path
from typing import Final, Literal


# Chemins des fichiers
DATA_DIR: Final[Path] = Path("data")
# Correction: Le fichier CSV se trouve dans data/csv/communes_departements.csv
CSV_FILE_PATH: Final[Path] = DATA_DIR / "csv" / "communes_departements.csv"

# Configuration CSV
CSV_ENCODING: Final[str] = "utf-8"
CSV_DELIMITER: Final[str] = ","
CSV_QUOTECHAR: Final[str] = '"'

# Noms des colonnes attendus dans le CSV
# Le CSV doit contenir au minimum ces colonnes
# Correction: Les noms de colonnes doivent correspondre au fichier CSV réel
CSV_COLUMN_REGION: Final[str] = "nom_region"
CSV_COLUMN_DEPARTMENT: Final[str] = "nom_departement"
CSV_COLUMN_CODE_DEPARTMENT: Final[str] = "code_departement"

# Colonnes pour les communes
CSV_COLUMN_CITY: Final[str] = "nom_commune"
CSV_COLUMN_CITY_CODE_POSTAL: Final[str] = "code_postal"
CSV_COLUMN_CITY_LATITUDE: Final[str] = "latitude"
CSV_COLUMN_CITY_LONGITUDE: Final[str] = "longitude"

# Configuration du traitement
BATCH_SIZE: Final[int] = 100  # Nombre d'objets à créer par batch

# Configuration de la gestion des doublons
DEFAULT_DUPLICATE_HANDLING: Final[Literal["skip", "replace"]] = "skip"
# Options de gestion des doublons:
# - "skip": Ignorer les communes existantes (défaut)
# - "replace": Remplacer les communes existantes

# Logging
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
