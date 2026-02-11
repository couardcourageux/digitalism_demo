"""
Script ETL pour générer un JSON structuré des régions et départements.

Ce script lit les fichiers CSV des régions et départements, normalise les données
et génère un fichier JSON structuré qui sera utilisé par une migration Alembic.

Usage:
    python -m src.etl.scripts.generate_regions_departments_json

Le JSON généré est stocké dans data/regions_departments.json
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Configuration
DATA_DIR: Path = Path("data")
CSV_FILE_PATH: Path = DATA_DIR / "csv" / "communes_departements.csv"
CSV_ENCODING: str = "utf-8"
CSV_DELIMITER: str = ","
CSV_QUOTECHAR: str = '"'
DATA_DIR: Path = Path("data")

# Noms des colonnes attendus dans le CSV
CSV_COLUMN_REGION: str = "nom_region"
CSV_COLUMN_DEPARTMENT: str = "nom_departement"
CSV_COLUMN_CODE_DEPARTMENT: str = "code_departement"


def clean_string(value: str) -> str:
    """
    Nettoie une chaîne de caractères en supprimant les espaces inutiles.

    Args:
        value: La chaîne à nettoyer

    Returns:
        La chaîne nettoyée
    """
    return value.strip() if value else ""


def normalize_name(value: str) -> str:
    """
    Normalise un nom en le mettant en majuscules et en nettoyant les espaces.

    Args:
        value: Le nom à normaliser

    Returns:
        Le nom normalisé en majuscules
    """
    return clean_string(value).upper()


def get_csv_value(row: Dict[str, str], column_name: str) -> str:
    """
    Récupère une valeur d'une ligne CSV en gérant les colonnes manquantes.

    Args:
        row: Dictionnaire représentant une ligne du CSV
        column_name: Nom de la colonne à récupérer

    Returns:
        La valeur nettoyée ou une chaîne vide si la colonne n'existe pas
    """
    return clean_string(row.get(column_name, ""))


def validate_data(regions_data: List[Dict[str, Any]]) -> bool:
    """
    Valide les données avant écriture.

    Args:
        regions_data: Liste des régions avec leurs départements

    Returns:
        True si les données sont valides, False sinon

    Raises:
        ValueError: Si les données sont invalides
    """
    if not regions_data:
        raise ValueError("Aucune région trouvée dans les données")

    for region in regions_data:
        if not region.get("nom"):
            raise ValueError("Une région sans nom a été trouvée")

        departements = region.get("departements", [])
        if not departements:
            raise ValueError(f"La région '{region['nom']}' n'a aucun département")

        for dept in departements:
            if not dept.get("code"):
                raise ValueError(f"Un département sans code a été trouvé dans la région '{region['nom']}'")
            if not dept.get("nom"):
                raise ValueError(f"Un département sans nom a été trouvé dans la région '{region['nom']}'")

    return True


def read_csv(file_path: Path) -> List[Dict[str, str]]:
    """
    Lit le fichier CSV et retourne les lignes sous forme de dictionnaires.

    Args:
        file_path: Chemin vers le fichier CSV

    Returns:
        Liste des lignes du CSV sous forme de dictionnaires

    Raises:
        FileNotFoundError: Si le fichier CSV n'existe pas
        IOError: Si une erreur de lecture survient
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier CSV n'existe pas: {file_path}")

    print(f"Lecture du fichier CSV: {file_path}")

    rows = []
    with open(file_path, "r", encoding=CSV_ENCODING, newline="") as csvfile:
        reader = csv.DictReader(
            csvfile,
            delimiter=CSV_DELIMITER,
            quotechar=CSV_QUOTECHAR,
        )

        # Vérifier que le fichier a des colonnes
        if not reader.fieldnames:
            raise ValueError("Le fichier CSV ne contient pas d'en-tête")

        print(f"Colonnes détectées: {list(reader.fieldnames)}")

        # Lire les lignes
        for row_number, row in enumerate(reader, start=1):
            rows.append(row)

        print(f"Fin de la lecture du fichier CSV ({row_number} lignes lues)")

    return rows


def extract_regions(rows: List[Dict[str, str]]) -> List[str]:
    """
    Extrait les régions uniques des données CSV.

    Args:
        rows: Liste des lignes du CSV

    Returns:
        Liste triée des noms de régions uniques
    """
    print("\n--- Extraction des régions ---")

    region_names: Set[str] = set()

    for row in rows:
        region_name = get_csv_value(row, CSV_COLUMN_REGION)
        if region_name:
            normalized_name = normalize_name(region_name)
            if normalized_name:
                region_names.add(normalized_name)

    regions = sorted(region_names)
    print(f"✓ {len(regions)} région(s) trouvée(s)")

    return regions


def extract_departments(rows: List[Dict[str, str]]) -> List[Tuple[str, str, str]]:
    """
    Extrait les départements uniques des données CSV.

    Args:
        rows: Liste des lignes du CSV

    Returns:
        Liste de tuples (code_departement, nom_departement, nom_region)
    """
    print("\n--- Extraction des départements ---")

    # Utiliser un dictionnaire pour stocker les départements uniques
    # Clé: (code_departement, region_name)
    departments_dict: Dict[Tuple[str, str], Tuple[str, str, str]] = {}

    for row in rows:
        department_name = get_csv_value(row, CSV_COLUMN_DEPARTMENT)
        code_departement = get_csv_value(row, CSV_COLUMN_CODE_DEPARTMENT)
        region_name = get_csv_value(row, CSV_COLUMN_REGION)

        # Vérifier que toutes les colonnes requises sont présentes
        if not department_name or not code_departement or not region_name:
            print(f"  ⚠ Ligne ignorée: données incomplètes "
                  f"(department={department_name}, code={code_departement}, region={region_name})")
            continue

        # Normaliser les données
        normalized_name = normalize_name(department_name)
        normalized_code = normalize_name(code_departement)
        normalized_region = normalize_name(region_name)

        if not normalized_name or not normalized_code or not normalized_region:
            print(f"  ⚠ Ligne ignorée: données invalides après normalisation "
                  f"(department={normalized_name}, code={normalized_code}, region={normalized_region})")
            continue

        # Créer la clé unique pour le département
        dept_key = (normalized_code, normalized_region)

        # Ajouter le département s'il n'existe pas déjà
        if dept_key not in departments_dict:
            departments_dict[dept_key] = (normalized_code, normalized_name, normalized_region)

    departments = list(departments_dict.values())
    print(f"✓ {len(departments)} département(s) trouvé(s)")

    return departments


def generate_json_structure(
    regions: List[str],
    departments: List[Tuple[str, str, str]]
) -> List[Dict[str, Any]]:
    """
    Génère la structure JSON attendue à partir des données extraites.

    Args:
        regions: Liste des noms de régions
        departments: Liste de tuples (code, nom, region_name)

    Returns:
        Liste des régions avec leurs départements au format JSON
    """
    print("\n--- Génération de la structure JSON ---")

    # Créer un dictionnaire pour regrouper les départements par région
    regions_dict: Dict[str, Dict[str, Any]] = {}

    # Initialiser les régions
    for region in regions:
        regions_dict[region] = {
            "nom": region,
            "departements": []
        }

    # Ajouter les départements à leur région respective
    for code, name, region_name in departments:
        if region_name in regions_dict:
            regions_dict[region_name]["departements"].append({
                "code": code,
                "nom": name
            })
        else:
            print(f"  ⚠ Attention: Département '{name}' ({code}) "
                  f"a une région '{region_name}' qui n'existe pas")

    # Trier les départements par code dans chaque région
    for region_data in regions_dict.values():
        region_data["departements"].sort(key=lambda d: d["code"])

    # Retourner la liste triée par nom de région
    return sorted(
        regions_dict.values(),
        key=lambda r: r["nom"]
    )


def main():
    """
    Fonction principale du script ETL.

    Cette fonction:
    1. Lit le fichier CSV
    2. Extrait les régions et départements
    3. Génère la structure JSON attendue
    4. Valide les données
    5. Écrit le JSON dans data/regions_departments.json
    """
    print("=" * 60)
    print("Génération du JSON des régions et départements")
    print("=" * 60)

    # Étape 1: Lecture du fichier CSV
    rows = read_csv(CSV_FILE_PATH)

    # Étape 2: Extraction des régions
    regions = extract_regions(rows)

    # Étape 3: Extraction des départements
    departments = extract_departments(rows)

    # Étape 4: Génération de la structure JSON
    regions_data = generate_json_structure(regions, departments)

    # Étape 5: Validation des données
    print("\n--- Validation des données ---")
    try:
        validate_data(regions_data)
        print("✓ Validation réussie")
    except ValueError as e:
        print(f"✗ Erreur de validation: {e}")
        raise

    # Étape 6: Écriture du fichier JSON
    output_path = DATA_DIR / "regions_departments.json"
    print(f"\n--- Écriture du fichier JSON ---")
    print(f"Chemin: {output_path}")

    # Créer le dossier data/ s'il n'existe pas
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Écrire le JSON avec indentation pour la lisibilité
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"regions": regions_data},
            f,
            ensure_ascii=False,
            indent=2
        )

    # Résumé
    print("\n" + "=" * 60)
    print("Résumé:")
    print(f"  - {len(regions)} région(s) trouvée(s)")
    print(f"  - {len(departments)} département(s) trouvé(s)")
    print(f"  - Fichier JSON généré: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nErreur lors de l'exécution: {e}")
        raise
