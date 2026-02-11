"""
Transformer pour extraire et transformer les communes depuis les données CSV.

Ce module implémente un transformer qui extrait les communes uniques
des données CSV et les transforme en objets CityData.
"""

from typing import Iterator, Dict, Any, Optional, Tuple, List

from src.etl.transformers.base_transformer import BaseTransformer
from src.etl.utils.data_models import CityData
from src.etl.utils.csv_helpers import get_csv_value, normalize_name
from src.etl.services.geo_api import GeoApiService, GeocodingResult


class CityTransformer(BaseTransformer[CityData]):
    """
    Transformer pour extraire les communes uniques des données CSV.

    Ce transformer parcourt les lignes du CSV pour extraire toutes les communes
    uniques (basées sur le nom + code postal), en nettoyant et normalisant
    les noms (mise en majuscules). Il extrait également les coordonnées GPS
    si elles sont disponibles dans le CSV.
    """

    def __init__(
        self,
        enable_geocoding: bool = False,
        geocoding_service: Optional[GeoApiService] = None,
    ):
        """
        Initialise le transformer de communes.

        Args:
            enable_geocoding: Si True, active le géocodage des villes sans coordonnées
            geocoding_service: Service de géocodage à utiliser (GeoApiService).
                              Si None, utilise GeoApiService par défaut.
        """
        super().__init__(component_name="city_transformer", entity_name="commune")
        self.enable_geocoding = enable_geocoding
        self.geocoding_service: Optional[GeoApiService] = None

        if self.enable_geocoding:
            if geocoding_service is not None:
                self.geocoding_service = geocoding_service
                service_name = type(geocoding_service).__name__
                self.logger.info(f"Service de géocodage activé (service personnalisé: {service_name})")
            else:
                self.geocoding_service = GeoApiService()
                self.logger.info("Service de géocodage activé (API Géo française)")

    def _extract_city_data(self, row: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
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

    def _normalize_city_data(self, city_name: str, code_postal: str, department_name: str) -> Optional[Tuple[str, str, str]]:
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

    def _extract_coordinates(self, row: Dict[str, Any], normalized_name: str) -> Tuple[Optional[float], Optional[float]]:
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

    def _geocode_city(self, city_name: str, code_postal: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Géocode une ville en utilisant le service de géocodage.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal

        Returns:
            Tuple (latitude, longitude) ou (None, None) si le géocodage échoue
        """
        if not self.geocoding_service:
            return None, None

        result: Optional[GeocodingResult] = self.geocoding_service.geocode(city_name, code_postal)

        if result:
            service_name = type(self.geocoding_service).__name__
            self.logger.info(
                f"Géocodage réussi pour {city_name} ({code_postal}): "
                f"{result.latitude}, {result.longitude} (source: {result.source}, service: {service_name})"
            )
            return result.latitude, result.longitude
        else:
            self.logger.warning(f"Échec du géocodage pour {city_name} ({code_postal})")
            return None, None

    def transform(self, data: Iterator[Dict[str, Any]], enable_geocoding: bool = False) -> List[CityData]:
        """
        Extrait les communes uniques des données CSV.

        Cette méthode parcourt toutes les lignes du CSV pour extraire
        les communes uniques (basées sur le nom + code postal).
        Les noms sont normalisés en majuscules. Les coordonnées GPS
        sont extraites si disponibles dans le CSV, sinon le géocodage
        est utilisé si activé.

        Args:
            data: Un itérateur de dictionnaires représentant les lignes du CSV
            enable_geocoding: Si True, active le géocodage des villes sans coordonnées

        Returns:
            Une liste de CityData représentant les communes uniques

        Raises:
            ValueError: Si aucune commune n'est trouvée dans les données
        """
        self._log_start("Début de la transformation des communes")

        # Utiliser un dictionnaire pour stocker les communes uniques
        # Clé: (nom_normalisé, code_postal)
        cities_dict: Dict[Tuple[str, str], CityData] = {}

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

            # Extraire les coordonnées GPS si disponibles dans le CSV
            latitude, longitude = self._extract_coordinates(row, normalized_name)

            # Si les coordonnées ne sont pas disponibles dans le CSV et que le géocodage est activé
            if latitude is None or longitude is None:
                if enable_geocoding or self.enable_geocoding:
                    # Utiliser le nom original (avant normalisation) pour le géocodage
                    geocoded_lat, geocoded_lon = self._geocode_city(city_name, code_postal)
                    if geocoded_lat is not None and geocoded_lon is not None:
                        latitude = geocoded_lat
                        longitude = geocoded_lon

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
