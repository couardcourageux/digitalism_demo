"""
Transformer pour extraire et transformer les départements depuis les données CSV.

Ce module implémente un transformer qui extrait les départements uniques
des données CSV et les transforme en objets DepartmentData.
"""

from typing import Iterator, Dict, Any

from src.etl.transformers.base_transformer import BaseTransformer
from src.etl.utils.data_models import DepartmentData
from src.etl.utils.csv_helpers import get_csv_value, normalize_name
from src.etl.config import (
    CSV_COLUMN_DEPARTMENT,
    CSV_COLUMN_CODE_DEPARTMENT,
    CSV_COLUMN_REGION,
)


class DepartmentTransformer(BaseTransformer[DepartmentData]):
    """
    Transformer pour extraire les départements uniques des données CSV.

    Ce transformer parcourt les lignes du CSV pour extraire tous les départements
    uniques, en nettoyant et normalisant les noms et codes de départements.
    Chaque département est associé à sa région d'appartenance.
    """

    def __init__(self):
        """
        Initialise le transformer de départements.
        """
        super().__init__(component_name="department_transformer", entity_name="département")

    def transform(self, data: Iterator[Dict[str, Any]]) -> list[DepartmentData]:
        """
        Extrait les départements uniques des données CSV.

        Cette méthode parcourt toutes les lignes du CSV pour extraire
        les départements uniques. Les noms et codes de départements
        sont nettoyés et normalisés (mise en majuscules, suppression des espaces).
        Chaque département est associé à sa région d'appartenance.

        Args:
            data: Un itérateur de dictionnaires représentant les lignes du CSV

        Returns:
            Une liste de DepartmentData représentant les départements uniques

        Raises:
            ValueError: Si aucun département n'est trouvé dans les données
        """
        self._log_start("Début de la transformation des départements")

        # Utiliser un dictionnaire pour stocker les départements uniques
        # Clé: (code_departement, region_name)
        departments_dict: dict[tuple[str, str], DepartmentData] = {}

        # Parcourir les données pour extraire les départements uniques
        for row in data:
            department_name = get_csv_value(row, CSV_COLUMN_DEPARTMENT)
            code_departement = get_csv_value(row, CSV_COLUMN_CODE_DEPARTMENT)
            region_name = get_csv_value(row, CSV_COLUMN_REGION)

            # Vérifier que toutes les colonnes requises sont présentes
            if not department_name or not code_departement or not region_name:
                self.logger.warning(
                    f"Ligne ignorée: données incomplètes "
                    f"(department={department_name}, code={code_departement}, region={region_name})"
                )
                continue

            # Normaliser les données
            normalized_name = normalize_name(department_name)
            normalized_code = normalize_name(code_departement)
            normalized_region = normalize_name(region_name)

            if not normalized_name or not normalized_code or not normalized_region:
                self.logger.warning(
                    f"Ligne ignorée: données invalides après normalisation "
                    f"(department={normalized_name}, code={normalized_code}, region={normalized_region})"
                )
                continue

            # Créer la clé unique pour le département
            dept_key = (normalized_code, normalized_region)

            # Ajouter le département s'il n'existe pas déjà
            if dept_key not in departments_dict:
                departments_dict[dept_key] = DepartmentData(
                    name=normalized_name,
                    code_departement=normalized_code,
                    region_name=normalized_region,
                )
            else:
                self.logger.debug(
                    f"Département en double détecté: {normalized_name} ({normalized_code}) "
                    f"dans la région {normalized_region}"
                )

        # Convertir le dictionnaire en liste
        departments = list(departments_dict.values())

        # Valider que le résultat n'est pas vide
        self._validate_result_not_empty(departments)

        # Log les départements trouvés
        self._log_transformed_items(
            departments,
            format_func=lambda d: f"{d.name} ({d.code_departement}) - {d.region_name}"
        )

        return departments
