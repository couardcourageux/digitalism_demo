"""
Pipeline ETL pour l'ingestion des communes.

Ce script orchestre le pipeline complet d'ingestion des communes:
- Extract: Lecture du fichier CSV
- Transform: Nettoyage et normalisation des données
- Load: Insertion en base de données
"""

import sys
import argparse
from pathlib import Path
from typing import Literal

from src.etl.extractors.csv_reader import CSVReader
from src.etl.transformers.city_transformer import CityTransformer
from src.etl.loaders.city_loader import CityLoader
from src.etl.config import CSV_FILE_PATH, DEFAULT_DUPLICATE_HANDLING
from src.database import get_etl_db


def run_city_etl_pipeline(
    duplicate_handling: Literal["skip", "replace"] = "skip",
    enable_geocoding: bool = False
) -> int:
    """
    Exécute le pipeline ETL complet pour l'ingestion des communes.

    Le pipeline suit les étapes suivantes:
    1. Extract: Lecture du fichier CSV contenant les communes
    2. Transform: Nettoyage et normalisation des données (uppercase, déduplication)
    3. Load: Insertion des communes en base de données

    Args:
        duplicate_handling: Stratégie de gestion des doublons
            - "skip": Ignorer les communes existantes (défaut)
            - "replace": Remplacer les communes existantes
        enable_geocoding: Si True, active le géocodage des villes sans coordonnées

    Returns:
        Le nombre de communes chargées avec succès

    Raises:
        FileNotFoundError: Si le fichier CSV n'existe pas
        ValueError: Si les données ne peuvent pas être transformées ou chargées
    """
    # Étape 1: Extract - Lecture du fichier CSV
    extractor = CSVReader(file_path=CSV_FILE_PATH)
    raw_data = extractor.read()

    # Étape 2: Transform - Nettoyage et normalisation des données
    transformer = CityTransformer(enable_geocoding=enable_geocoding)
    cities = transformer.transform(raw_data, enable_geocoding=enable_geocoding)

    # Étape 3: Load - Insertion en base de données
    db = get_etl_db()
    try:
        loader = CityLoader(db, duplicate_handling=duplicate_handling)
        count = loader.load(cities)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return count


if __name__ == "__main__":
    # Configuration de l'analyseur d'arguments de ligne de commande
    parser = argparse.ArgumentParser(
        description="Pipeline ETL pour l'ingestion des communes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  # Import avec gestion des doublons par défaut (skip)
  python -m src.etl.scripts.city_etl_pipeline

  # Import en ignorant les doublons
  python -m src.etl.scripts.city_etl_pipeline --duplicate-handling skip

  # Import en remplaçant les doublons
  python -m src.etl.scripts.city_etl_pipeline --duplicate-handling replace
        """
    )

    parser.add_argument(
        "--duplicate-handling",
        choices=["skip", "replace"],
        default=DEFAULT_DUPLICATE_HANDLING,
        help=(
            "Stratégie de gestion des doublons:\n"
            "  skip: Ignorer les communes existantes (défaut)\n"
            "  replace: Remplacer les communes existantes"
        )
    )

    parser.add_argument(
        "--enable-geocoding",
        action="store_true",
        help="Active le géocodage des villes sans coordonnées via l'API Nominatim"
    )

    args = parser.parse_args()

    try:
        count = run_city_etl_pipeline(
            duplicate_handling=args.duplicate_handling,
            enable_geocoding=args.enable_geocoding
        )
        sys.exit(0)
    except Exception as e:
        print(f"Erreur lors de l'exécution du pipeline ETL: {e}", file=sys.stderr)
        sys.exit(1)
