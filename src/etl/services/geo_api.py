"""
Service de géocodage utilisant l'API Géo française.

Ce module fournit un service pour géocoder les villes en utilisant l'API Géo française
(geo.api.gouv.fr). Il implémente un cache persistant pour les données de l'API Géo
et les résultats de géocodage.
"""

import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List

import requests

from src.etl.config import (
    GEO_API_BASE_URL,
    GEO_API_CACHE_FILE,
    GEO_API_FORCE_REFRESH,
    GEO_API_MAX_RETRIES,
    GEO_API_RETRY_DELAY,
)


logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    """
    Résultat d'une requête de géocodage.

    Attributes:
        latitude: Latitude de la ville
        longitude: Longitude de la ville
        source: Source des données ('geo_api')
        display_name: Nom complet de la ville (ex: "Paris, France")
        city: Nom de la ville
        postcode: Code postal
    """
    latitude: float
    longitude: float
    source: str  # 'geo_api'
    display_name: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None


@dataclass
class CommuneGeoApi:
    """
    Modèle de données pour une commune issue de l'API Géo.

    Attributes:
        nom: Nom de la commune
        code: Code INSEE de la commune
        centre: Coordonnées GPS au format GeoJSON
    """
    nom: str
    code: str
    centre: Dict[str, Any]

    def get_postal_code(self) -> str:
        """
        Génère le code postal à partir du code INSEE.

        Le code postal est généralement les 5 premiers chiffres du code INSEE,
        mais pour les communes avec plusieurs codes postaux, ce n'est pas toujours exact.

        Returns:
            Code postal sur 5 chiffres
        """
        # Pour les communes de métropole, le code postal est généralement
        # les 5 premiers chiffres du code INSEE
        return self.code[:5]


class GeoApiService:
    """
    Service de géocodage utilisant l'API Géo française.

    Ce service fournit des fonctionnalités de géocodage avec:
    - Cache local des données de l'API Géo (téléchargées une fois)
    - Cache persistant pour les résultats de géocodage
    - Gestion des erreurs avec retry
    """

    def __init__(
        self,
        base_url: str = GEO_API_BASE_URL,
        cache_file: Path = GEO_API_CACHE_FILE,
        force_refresh: bool = GEO_API_FORCE_REFRESH,
        max_retries: int = GEO_API_MAX_RETRIES,
        retry_delay: float = GEO_API_RETRY_DELAY,
    ):
        """
        Initialise le service de géocodage API Géo.

        Args:
            base_url: URL de base de l'API Géo
            cache_file: Chemin du fichier de cache des communes
            force_refresh: Force le rechargement des données de l'API
            max_retries: Nombre maximum de tentatives en cas d'erreur
            retry_delay: Délai entre les tentatives (en secondes)
        """
        self.base_url = base_url
        self.cache_file = cache_file
        self.force_refresh = force_refresh
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Cache des communes de l'API Géo
        self._communes_cache: Dict[str, CommuneGeoApi] = {}
        # Index pour la recherche par nom normalisé
        self._communes_by_name: Dict[str, List[CommuneGeoApi]] = {}

        # Charger les données de l'API Géo
        self._load_communes_data()

    def _normalize_string(self, text: str) -> str:
        """
        Normalise une chaîne de caractères pour la comparaison.

        Convertit en minuscules, retire les accents et les espaces superflus.

        Args:
            text: Texte à normaliser

        Returns:
            Texte normalisé
        """
        # Convertir en minuscules
        text = text.lower().strip()
        # Retirer les accents
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        # Remplacer les tirets et espaces par des espaces
        text = re.sub(r'[-\s]+', ' ', text)
        return text

    def _load_communes_data(self) -> None:
        """
        Charge les données des communes depuis le cache ou les télécharge depuis l'API.

        Si le fichier de cache existe et que force_refresh est False,
        charge les données depuis le fichier. Sinon, télécharge les données
        depuis l'API Géo et les stocke dans le cache.
        """
        # Vérifier si le cache existe et si on doit le recharger
        if self.cache_file.exists() and not self.force_refresh:
            self._load_communes_from_cache()
        else:
            self._download_communes_from_api()

    def _load_communes_from_cache(self) -> None:
        """
        Charge les données des communes depuis le fichier de cache.
        """
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parser les données et créer les objets CommuneGeoApi
            for commune_data in data:
                commune = CommuneGeoApi(
                    nom=commune_data["nom"],
                    code=commune_data["code"],
                    centre=commune_data["centre"],
                )
                self._add_commune_to_index(commune)

            logger.info(f"Cache API Géo chargé: {len(self._communes_cache)} communes")
        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Erreur lors du chargement du cache API Géo: {e}")
            logger.info("Téléchargement des données depuis l'API...")
            self._download_communes_from_api()

    def _download_communes_from_api(self) -> None:
        """
        Télécharge les données des communes depuis l'API Géo.

        Télécharge toutes les communes de France métropolitaine et d'outre-mer
        et les stocke dans le cache local.
        """
        logger.info("Téléchargement des communes depuis l'API Géo...")

        try:
            # Télécharger toutes les communes
            communes_data = self._make_geo_api_request()

            if not communes_data:
                logger.error("Aucune donnée reçue de l'API Géo")
                return

            # Créer le répertoire parent si nécessaire
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Sauvegarder les données dans le cache
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(communes_data, f, ensure_ascii=False, indent=2)

            # Parser les données et créer les objets CommuneGeoApi
            for commune_data in communes_data:
                commune = CommuneGeoApi(
                    nom=commune_data["nom"],
                    code=commune_data["code"],
                    centre=commune_data["centre"],
                )
                self._add_commune_to_index(commune)

            logger.info(f"Cache API Géo téléchargé et sauvegardé: {len(self._communes_cache)} communes")

        except requests.RequestException as e:
            logger.error(f"Erreur lors du téléchargement des communes depuis l'API Géo: {e}")

    def _add_commune_to_index(self, commune: CommuneGeoApi) -> None:
        """
        Ajoute une commune aux index de recherche.

        Args:
            commune: Commune à ajouter
        """
        # Index par code INSEE
        self._communes_cache[commune.code] = commune

        # Index par nom normalisé
        normalized_name = self._normalize_string(commune.nom)
        if normalized_name not in self._communes_by_name:
            self._communes_by_name[normalized_name] = []
        self._communes_by_name[normalized_name].append(commune)

    def _make_geo_api_request(self) -> List[Dict[str, Any]]:
        """
        Effectue une requête à l'API Géo avec retry.

        Returns:
            Liste des communes au format JSON

        Raises:
            requests.RequestException: Si la requête échoue après tous les retries
        """
        url = f"{self.base_url}?fields=nom,code,centre&format=json&boost=population"

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Requête API Géo (tentative {attempt}/{self.max_retries})...")
                response = requests.get(url, timeout=60)

                # Vérifier le code de statut HTTP
                response.raise_for_status()

                return response.json()

            except requests.RequestException as e:
                last_exception = e
                logger.warning(
                    f"Erreur lors de la requête API Géo (tentative {attempt}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)  # Backoff exponentiel

        # Si on arrive ici, toutes les tentatives ont échoué
        raise requests.RequestException(
            f"Échec après {self.max_retries} tentatives: {last_exception}"
        )

    def _find_commune_by_name(self, city_name: str, code_postal: str) -> Optional[CommuneGeoApi]:
        """
        Recherche une commune par nom et code postal.

        Args:
            city_name: Nom de la commune
            code_postal: Code postal

        Returns:
            CommuneGeoApi si trouvée, None sinon
        """
        normalized_name = self._normalize_string(city_name)
        code_postal_clean = code_postal.strip().zfill(5)

        # Rechercher les communes avec le même nom normalisé
        communes = self._communes_by_name.get(normalized_name, [])

        if not communes:
            return None

        # Si une seule commune correspond, la retourner
        if len(communes) == 1:
            return communes[0]

        # Si plusieurs communes ont le même nom, utiliser le code postal pour filtrer
        for commune in communes:
            # Générer le code postal possible depuis le code INSEE
            commune_postal = commune.get_postal_code()
            if commune_postal == code_postal_clean:
                return commune

        # Si aucune correspondance exacte, essayer une correspondance partielle
        # (pour les communes avec plusieurs codes postaux)
        for commune in communes:
            commune_postal = commune.get_postal_code()
            if commune_postal.startswith(code_postal_clean[:2]):
                return commune

        # Retourner la première commune si aucune correspondance exacte
        logger.debug(
            f"Plusieurs communes trouvées pour {city_name}, "
            f"utilisation de la première: {communes[0].nom} ({communes[0].code})"
        )
        return communes[0]

    def _commune_to_geocoding_result(self, commune: CommuneGeoApi, source: str = "geo_api") -> GeocodingResult:
        """
        Convertit une CommuneGeoApi en GeocodingResult.

        Args:
            commune: Commune à convertir
            source: Source des données ('geo_api')

        Returns:
            GeocodingResult
        """
        # Extraire les coordonnées depuis le format GeoJSON
        # Format: {"type": "Point", "coordinates": [longitude, latitude]}
        coordinates = commune.centre.get("coordinates", [0, 0])
        longitude = float(coordinates[0])
        latitude = float(coordinates[1])

        return GeocodingResult(
            latitude=latitude,
            longitude=longitude,
            source=source,
            display_name=f"{commune.nom}, France",
            city=commune.nom,
            postcode=commune.get_postal_code(),
        )

    def geocode(self, city_name: str, code_postal: str) -> Optional[GeocodingResult]:
        """
        Géocode une ville en utilisant l'API Géo.

        Cette méthode cherche la commune dans les données de l'API Géo.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal

        Returns:
            GeocodingResult si le géocodage réussit, None sinon
        """
        # Vérifier si le cache des communes est disponible
        if not self._communes_cache:
            logger.warning("Cache des communes vide, impossible de géocoder")
            return None

        # Rechercher la commune dans l'API Géo
        commune = self._find_commune_by_name(city_name, code_postal)

        if commune:
            logger.info(
                f"Géocodage réussi pour {city_name} ({code_postal}) "
                f"via API Géo: {commune.centre['coordinates'][1]}, {commune.centre['coordinates'][0]}"
            )
            return self._commune_to_geocoding_result(commune, source="geo_api")

        logger.warning(
            f"Commune non trouvée dans l'API Géo: {city_name} ({code_postal})"
        )
        return None

    def refresh_communes_data(self) -> None:
        """
        Force le rechargement des données des communes depuis l'API Géo.

        Cette méthode télécharge à nouveau les données depuis l'API et
        met à jour le cache local.
        """
        logger.info("Force du rechargement des données des communes...")
        self.force_refresh = True
        self._communes_cache.clear()
        self._communes_by_name.clear()
        self._load_communes_data()
        self.force_refresh = False
        logger.info("Rechargement des communes terminé")

    def get_communes_count(self) -> int:
        """
        Retourne le nombre de communes dans le cache.

        Returns:
            Nombre de communes
        """
        return len(self._communes_cache)

    def is_cache_loaded(self) -> bool:
        """
        Vérifie si le cache des communes est chargé.

        Returns:
            True si le cache est chargé, False sinon
        """
        return len(self._communes_cache) > 0
