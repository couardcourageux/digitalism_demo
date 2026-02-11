"""
Service de géocodage utilisant l'API Nominatim.

Ce module fournit un service pour géocoder les villes en utilisant l'API OpenStreetMap Nominatim.
Il implémente un cache persistant, un rate limiting et une gestion des erreurs avec retry.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict
from urllib.parse import urlencode

import requests

from src.etl.config import (
    NOMINATIM_BASE_URL,
    NOMINATIM_USER_AGENT,
    NOMINATIM_RATE_LIMIT,
    NOMINATIM_CACHE_FILE,
    NOMINATIM_MAX_RETRIES,
    NOMINATIM_RETRY_DELAY,
)


logger = logging.getLogger(__name__)


@dataclass
class GeocodingResult:
    """
    Résultat d'une requête de géocodage.

    Attributes:
        latitude: Latitude de la ville
        longitude: Longitude de la ville
        source: Source des données ('cache', 'api')
        display_name: Nom complet de la ville (ex: "Paris, Île-de-France, France")
        city: Nom de la ville
        postcode: Code postal
    """
    latitude: float
    longitude: float
    source: str  # 'cache' ou 'api'
    display_name: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None


class GeocodingService:
    """
    Service de géocodage utilisant l'API Nominatim.

    Ce service fournit des fonctionnalités de géocodage avec:
    - Cache persistant (fichier JSON)
    - Rate limiting (1 req/s par défaut)
    - Gestion des erreurs avec retry
    """

    def __init__(
        self,
        base_url: str = NOMINATIM_BASE_URL,
        user_agent: str = NOMINATIM_USER_AGENT,
        rate_limit: float = NOMINATIM_RATE_LIMIT,
        cache_file: Path = NOMINATIM_CACHE_FILE,
        max_retries: int = NOMINATIM_MAX_RETRIES,
        retry_delay: float = NOMINATIM_RETRY_DELAY,
    ):
        """
        Initialise le service de géocodage.

        Args:
            base_url: URL de base de l'API Nominatim
            user_agent: User-Agent pour les requêtes HTTP
            rate_limit: Délai minimum entre les requêtes (en secondes)
            cache_file: Chemin du fichier de cache
            max_retries: Nombre maximum de tentatives en cas d'erreur
            retry_delay: Délai entre les tentatives (en secondes)
        """
        self.base_url = base_url
        self.user_agent = user_agent
        self.rate_limit = rate_limit
        self.cache_file = cache_file
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0.0

        # Charger le cache depuis le fichier
        self._load_cache()

    def _load_cache(self) -> None:
        """
        Charge le cache depuis le fichier JSON.

        Si le fichier n'existe pas, initialise un cache vide.
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Cache de géocodage chargé: {len(self._cache)} entrées")
            else:
                self._cache = {}
                logger.info("Fichier de cache inexistant, cache initialisé comme vide")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Erreur lors du chargement du cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """
        Sauvegarde le cache dans le fichier JSON.

        Crée le répertoire parent si nécessaire.
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache de géocodage sauvegardé: {len(self._cache)} entrées")
        except IOError as e:
            logger.warning(f"Erreur lors de la sauvegarde du cache: {e}")

    def _get_cache_key(self, city_name: str, code_postal: str) -> str:
        """
        Génère une clé de cache pour une ville.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal

        Returns:
            Clé de cache unique
        """
        return f"{city_name.lower()}_{code_postal}"

    def _get_from_cache(self, city_name: str, code_postal: str) -> Optional[GeocodingResult]:
        """
        Récupère un résultat depuis le cache.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal

        Returns:
            GeocodingResult si trouvé dans le cache, None sinon
        """
        cache_key = self._get_cache_key(city_name, code_postal)
        cached_data = self._cache.get(cache_key)

        if cached_data:
            logger.debug(f"Cache hit pour {city_name} ({code_postal})")
            return GeocodingResult(
                latitude=cached_data["latitude"],
                longitude=cached_data["longitude"],
                source="cache",
                display_name=cached_data.get("display_name"),
                city=cached_data.get("city"),
                postcode=cached_data.get("postcode"),
            )

        return None

    def _save_to_cache(self, city_name: str, code_postal: str, result: GeocodingResult) -> None:
        """
        Sauvegarde un résultat dans le cache.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal
            result: Résultat de géocodage à sauvegarder
        """
        cache_key = self._get_cache_key(city_name, code_postal)
        self._cache[cache_key] = {
            "latitude": result.latitude,
            "longitude": result.longitude,
            "display_name": result.display_name,
            "city": result.city,
            "postcode": result.postcode,
        }
        self._save_cache()

    def _wait_for_rate_limit(self) -> None:
        """
        Attend si nécessaire pour respecter le rate limiting.

        Cette méthode s'assure qu'il y a au moins `rate_limit` secondes
        entre deux requêtes successives.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            logger.debug(f"Rate limiting: attente de {sleep_time:.2f} secondes")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_nominatim_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Nominatim avec retry.

        Args:
            params: Paramètres de la requête

        Returns:
            Réponse JSON de l'API

        Raises:
            requests.RequestException: Si la requête échoue après tous les retries
        """
        url = f"{self.base_url}/search?{urlencode(params)}"
        headers = {"User-Agent": self.user_agent}

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self._wait_for_rate_limit()
                response = requests.get(url, headers=headers, timeout=10)

                # Vérifier le code de statut HTTP
                response.raise_for_status()

                return response.json()

            except requests.RequestException as e:
                last_exception = e
                logger.warning(
                    f"Erreur lors de la requête Nominatim (tentative {attempt}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)  # Backoff exponentiel

        # Si on arrive ici, toutes les tentatives ont échoué
        raise requests.RequestException(
            f"Échec après {self.max_retries} tentatives: {last_exception}"
        )

    def geocode(self, city_name: str, code_postal: str) -> Optional[GeocodingResult]:
        """
        Géocode une ville en utilisant l'API Nominatim.

        Cette méthode vérifie d'abord le cache, puis fait une requête à l'API
        si nécessaire. Le résultat est mis en cache pour les requêtes futures.

        Args:
            city_name: Nom de la ville
            code_postal: Code postal

        Returns:
            GeocodingResult si le géocodage réussit, None sinon
        """
        # Vérifier le cache d'abord
        cached_result = self._get_from_cache(city_name, code_postal)
        if cached_result is not None:
            return cached_result

        # Préparer les paramètres de la requête
        params = {
            "city": city_name,
            "postalcode": code_postal,
            "country": "fr",
            "format": "json",
            "limit": "1",
            "addressdetails": "1",
        }

        logger.info(f"Géocodage de {city_name} ({code_postal}) via API Nominatim")

        try:
            # Faire la requête à l'API
            response_data = self._make_nominatim_request(params)

            # Vérifier que nous avons reçu des résultats
            if not response_data:
                logger.warning(f"Aucun résultat trouvé pour {city_name} ({code_postal})")
                return None

            # Extraire le premier résultat
            result_data = response_data[0]

            # Extraire les coordonnées
            latitude = float(result_data["lat"])
            longitude = float(result_data["lon"])

            # Extraire les informations supplémentaires
            address = result_data.get("address", {})
            display_name = result_data.get("display_name")
            city = address.get("city") or address.get("town") or address.get("village") or city_name
            postcode = address.get("postcode") or code_postal

            # Créer le résultat
            result = GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                source="api",
                display_name=display_name,
                city=city,
                postcode=postcode,
            )

            # Sauvegarder dans le cache
            self._save_to_cache(city_name, code_postal, result)

            logger.info(f"Géocodage réussi pour {city_name} ({code_postal}): {latitude}, {longitude}")
            return result

        except requests.RequestException as e:
            logger.error(f"Erreur de géocodage pour {city_name} ({code_postal}): {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Erreur lors du parsing de la réponse pour {city_name} ({code_postal}): {e}")
            return None
