"""
Configuration pour les modules ETL.

Ce module contient toutes les configurations nécessaires pour le pipeline ETL,
y compris les chemins des fichiers, l'encodage et les paramètres de traitement.
"""

from pathlib import Path
from typing import Final


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

# Configuration du traitement
BATCH_SIZE: Final[int] = 100  # Nombre d'objets à créer par batch
SKIP_DUPLICATES: Final[bool] = True  # Ignorer les doublons lors de l'insertion

# Logging
LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
