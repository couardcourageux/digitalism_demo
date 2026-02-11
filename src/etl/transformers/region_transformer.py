"""
Transformer pour extraire et transformer les régions depuis les données CSV.

Ce module implémente un transformer qui extrait les régions uniques
des données CSV et les transforme en objets RegionData.
"""

from typing import Iterator, Dict, Any

from src.etl.transformers.base_transformer import BaseTransformer
from src.etl.utils.data_models import RegionData
from src.etl.utils.csv_helpers import get_csv_value, normalize_name
from src.etl.config import CSV_COLUMN_REGION


class RegionTransformer(BaseTransformer[RegionData]):
    """
    Transformer pour extraire les régions uniques des données CSV.

    Ce transformer parcourt les lignes du CSV pour extraire toutes les régions
    uniques, en nettoyant et normalisant les noms de régions.
    """

    def __init__(self):
        """
        Initialise le transformer de régions.
        """
        super().__init__(component_name="region_transformer", entity_name="région")

    def transform(self, data: Iterator[Dict[str, Any]]) -> list[RegionData]:
        """
        Extrait les régions uniques des données CSV.

        Cette méthode parcourt toutes les lignes du CSV pour extraire
        les régions uniques. Les noms de régions sont nettoyés et normalisés
        (mise en majuscules, suppression des espaces).

        Args:
            data: Un itérateur de dictionnaires représentant les lignes du CSV

        Returns:
            Une liste de RegionData représentant les régions uniques

        Raises:
            ValueError: Si aucune région n'est trouvée dans les données
        """
        self._log_start("Début de la transformation des régions")

        # Utiliser un set pour stocker les noms de régions uniques
        region_names = set()

        # Parcourir les données pour extraire les régions uniques
        for row in data:
            region_name = get_csv_value(row, CSV_COLUMN_REGION)
            if region_name:
                normalized_name = normalize_name(region_name)
                if normalized_name:
                    region_names.add(normalized_name)

        # Créer les objets RegionData
        regions = [RegionData(name=name) for name in sorted(region_names)]

        # Valider que le résultat n'est pas vide
        self._validate_result_not_empty(regions)

        # Log les régions trouvées
        self._log_transformed_items(regions, format_func=lambda r: r.name)

        return regions
