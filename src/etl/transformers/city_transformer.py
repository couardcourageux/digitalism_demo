"""
Transformer pour extraire et transformer les communes depuis les données CSV.

Ce module implémente un transformer qui extrait les communes uniques
des données CSV et les transforme en objets CityData.
"""

from typing import Iterator, Dict, Any

from src.etl.transformers.base_transformer import BaseTransformer
from src.etl.utils.data_models import CityData
from src.etl.utils.csv_helpers import get_csv_value, normalize_name


class CityTransformer(BaseTransformer[CityData]):
    """
    Transformer pour extraire les communes uniques des données CSV.

    Ce transformer parcourt les lignes du CSV pour extraire toutes les communes
    uniques (basées sur le nom + code postal), en nettoyant et normalisant
    les noms (mise en majuscules). Il extrait également les coordonnées GPS
    si elles sont disponibles dans le CSV.
    """

    def __init__(self):
        """
        Initialise le transformer de communes.
        """
        super().__init__(component_name="city_transformer", entity_name="commune")

    def _extract_city_data(self, row: Dict[str, Any]) -> tuple[str, str, str] | None:
        """
        Extrait et valide les données de base d'une commune depuis une ligne CSV.

        Args:
            row: Dictionnaire représentant une ligne du CSV

        Returns:
            Tuple (city_name, code_postal, department_name) ou None si données invalides
        """
        city_name = get_csv_value(row, "nom_commune")
        code_postal = get_csv_value(row, "code_postal")
        department_name = get_csv_value(row, "nom_departement")

        # Vérifier que les colonnes requises sont présentes
        if not city_name or not code_postal:
            self.logger.warning(
                f"Ligne ignorée: données incomplètes "
                f"(city={city_name}, code_postal={code_postal})"
            )
            return None

        return city_name, code_postal, department_name

    def _normalize_city_data(self, city_name: str, code_postal: str, department_name: str) -> tuple[str, str, str] | None:
        """
        Normalise les données de la commune.

        Args:
            city_name: Nom de la commune
            code_postal: Code postal
            department_name: Nom du département

        Returns:
            Tuple (normalized_name, normalized_code, normalized_dept) ou None si données invalides
        """
        normalized_name = normalize_name(city_name)
        normalized_code = code_postal.strip().zfill(5)  # Pad avec des zéros à gauche pour avoir exactement 5 caractères
        normalized_dept = normalize_name(department_name) if department_name else None

        if not normalized_name or not normalized_code:
            self.logger.warning(
                f"Ligne ignorée: données invalides après normalisation "
                f"(city={normalized_name}, code_postal={normalized_code})"
            )
            return None

        return normalized_name, normalized_code, normalized_dept

    def _extract_coordinates(self, row: Dict[str, Any], normalized_name: str) -> tuple[float | None, float | None]:
        """
        Extrait les coordonnées GPS depuis une ligne CSV.

        Args:
            row: Dictionnaire représentant une ligne du CSV
            normalized_name: Nom normalisé de la commune (pour le logging)

        Returns:
            Tuple (latitude, longitude)
        """
        latitude = None
        longitude = None
        try:
            lat_str = get_csv_value(row, "latitude")
            lon_str = get_csv_value(row, "longitude")
            if lat_str:
                latitude = float(lat_str)
            if lon_str:
                longitude = float(lon_str)
        except (ValueError, TypeError) as e:
            self.logger.debug(
                f"Impossible de parser les coordonnées GPS pour {normalized_name}: {e}"
            )

        return latitude, longitude

    def transform(self, data: Iterator[Dict[str, Any]]) -> list[CityData]:
        """
        Extrait les communes uniques des données CSV.

        Cette méthode parcourt toutes les lignes du CSV pour extraire
        les communes uniques (basées sur le nom + code postal).
        Les noms sont normalisés en majuscules. Les coordonnées GPS
        sont extraites si disponibles.

        Args:
            data: Un itérateur de dictionnaires représentant les lignes du CSV

        Returns:
            Une liste de CityData représentant les communes uniques

        Raises:
            ValueError: Si aucune commune n'est trouvée dans les données
        """
        self._log_start("Début de la transformation des communes")

        # Utiliser un dictionnaire pour stocker les communes uniques
        # Clé: (nom_normalisé, code_postal)
        cities_dict: dict[tuple[str, str], CityData] = {}

        # Parcourir les données pour extraire les communes uniques
        for row in data:
            # Extraire les données de base
            city_data = self._extract_city_data(row)
            if city_data is None:
                continue
            city_name, code_postal, department_name = city_data

            # Normaliser les données
            normalized_data = self._normalize_city_data(city_name, code_postal, department_name)
            if normalized_data is None:
                continue
            normalized_name, normalized_code, normalized_dept = normalized_data

            # Créer la clé unique pour la commune (nom + code postal)
            city_key = (normalized_name, normalized_code)

            # Extraire les coordonnées GPS si disponibles
            latitude, longitude = self._extract_coordinates(row, normalized_name)

            # Ajouter la commune si elle n'existe pas déjà
            if city_key not in cities_dict:
                cities_dict[city_key] = CityData(
                    name=normalized_name,
                    code_postal=normalized_code,
                    department_name=normalized_dept,
                    latitude=latitude,
                    longitude=longitude,
                )
            else:
                self.logger.debug(
                    f"Commune en double détectée: {normalized_name} ({normalized_code})"
                )

        # Convertir le dictionnaire en liste
        cities = list(cities_dict.values())

        # Valider que le résultat n'est pas vide
        self._validate_result_not_empty(cities)

        # Log les communes trouvées
        self._log_transformed_items(
            cities,
            format_func=lambda c: f"{c.name} ({c.code_postal})"
        )

        return cities
