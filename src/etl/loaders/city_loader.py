"""
Loader pour les communes (City) dans le pipeline ETL.

Ce module implémente un loader qui charge les communes transformées
en base de données en utilisant le CityRepository.
"""

from typing import List, Literal
from sqlalchemy.orm import Session

from src.etl.loaders.base_loader import BaseLoader
from src.etl.utils.data_models import CityData
from src.model.city import City
from src.repository.city import CityRepository
from src.repository.department import DepartmentRepository
from src.schemas.city import CityCreate, CityUpdate


class CityLoader(BaseLoader[CityData]):
    """
    Loader pour les communes.

    Ce loader est responsable de charger les communes transformées
    en base de données. Il résout les department_id depuis les codes postaux
    et utilise CityRepository pour l'insertion ou la mise à jour.

    Attributes:
        db: Session de base de données
        city_repository: Repository pour les communes
        department_repository: Repository pour les départements
        duplicate_handling: Stratégie de gestion des doublons ("skip" ou "replace")
    """

    def __init__(self, db: Session, duplicate_handling: Literal["skip", "replace"] = "skip"):
        """
        Initialise le loader de communes.

        Args:
            db: Session de base de données
            duplicate_handling: Stratégie de gestion des doublons
                - "skip": Ignorer les communes existantes (défaut)
                - "replace": Remplacer les communes existantes
        """
        super().__init__(component_name="city_loader", entity_name="commune")
        self.db = db
        self.city_repository = CityRepository(db)
        self.department_repository = DepartmentRepository(db)
        self.duplicate_handling = duplicate_handling

    def _prepare_departments(self, data: List[CityData]) -> dict:
        """
        Prépare et valide les départements nécessaires pour les communes.

        Args:
            data: Liste des communes à charger

        Returns:
            Dictionnaire des départements indexés par code
        """
        # Récupérer tous les codes départements uniques nécessaires
        code_departements = set()
        for city_data in data:
            code_departement = City.calculate_department_from_postal_code(city_data.code_postal)
            code_departements.add(code_departement)

        # Récupérer tous les départements nécessaires en une seule requête
        departments = {}
        if code_departements:
            departments = self.department_repository.get_by_codes(list(code_departements))

            # Avertir si certains départements n'existent pas (ne pas lever d'erreur)
            missing_departments = code_departements - set(departments.keys())
            if missing_departments:
                warning_msg = f"Départements non trouvés (ignorés): {', '.join(missing_departments)}"
                self.logger.warning(warning_msg)

        return departments

    def _prepare_cities(self, data: List[CityData], departments: dict) -> List[dict]:
        """
        Convertit les CityData en dictionnaires pour le chargement.

        Args:
            data: Liste des communes à charger
            departments: Dictionnaire des départements indexés par code

        Returns:
            Liste des dictionnaires de communes à traiter
        """
        cities_to_process = []
        skipped_no_dept = 0
        
        for city_data in data:
            code_departement = City.calculate_department_from_postal_code(city_data.code_postal)
            
            # Vérifier que le département existe
            if code_departement not in departments:
                skipped_no_dept += 1
                continue
            
            department_id = departments[code_departement].id

            city_dict = {
                "name": city_data.name.upper(),  # Assurer l'uppercase
                "code_postal": city_data.code_postal,
                "department_id": department_id,
            }

            # Ajouter les coordonnées GPS si disponibles
            if city_data.latitude is not None:
                city_dict["latitude"] = city_data.latitude
            if city_data.longitude is not None:
                city_dict["longitude"] = city_data.longitude

            cities_to_process.append(city_dict)
        
        if skipped_no_dept > 0:
            self.logger.warning(f"{skipped_no_dept} commune(s) ignorée(s) car le département n'existe pas")

        return cities_to_process

    def _process_skip_mode(self, cities_to_process: List[dict]) -> int:
        """
        Traite les communes en mode skip (ignorer les doublons).

        Args:
            cities_to_process: Liste des dictionnaires de communes à traiter

        Returns:
            Nombre de communes créées
        """
        # Charger toutes les villes existantes en une seule requête pour optimiser
        from sqlalchemy import select
        stmt = select(City).where(City.deleted_at.is_(None))
        existing_cities = list(self.db.execute(stmt).scalars().all())
        
        # Créer un dictionnaire pour une recherche rapide
        existing_dict = {(c.name, c.code_postal): c for c in existing_cities}
        
        count = 0
        skipped = 0
        for city_dict in cities_to_process:
            key = (city_dict["name"], city_dict["code_postal"])
            if key in existing_dict:
                skipped += 1
            else:
                self.city_repository.create(city_dict)
                count += 1
        self._log_success(count, f"{count} commune(s) chargée(s) avec succès, {skipped} doublon(s) ignoré(s)")
        return count

    def _process_replace_mode(self, cities_to_process: List[dict]) -> int:
        """
        Traite les communes en mode replace (remplacer les doublons).

        Args:
            cities_to_process: Liste des dictionnaires de communes à traiter

        Returns:
            Nombre total de communes traitées (créées + mises à jour)
        """
        # Charger toutes les villes existantes en une seule requête pour optimiser
        from sqlalchemy import select
        stmt = select(City).where(City.deleted_at.is_(None))
        existing_cities = list(self.db.execute(stmt).scalars().all())
        
        # Créer un dictionnaire pour une recherche rapide
        existing_dict = {(c.name, c.code_postal): c for c in existing_cities}
        
        count = 0
        updated = 0
        for city_dict in cities_to_process:
            key = (city_dict["name"], city_dict["code_postal"])
            if key in existing_dict:
                # Mettre à jour la commune existante
                existing = existing_dict[key]
                update_data = CityUpdate(**city_dict)
                self.city_repository.update(existing, update_data)
                updated += 1
            else:
                # Créer la nouvelle commune
                self.city_repository.create(city_dict)
                count += 1
        self._log_success(count, f"{count} commune(s) créée(s), {updated} commune(s) mise(s) à jour")
        return count + updated

    def load(self, data: List[CityData]) -> int:
        """
        Charge les communes en base de données.

        Cette méthode convertit les CityData en objets CityCreate,
        résout les department_id depuis les codes postaux,
        et utilise CityRepository pour l'insertion ou la mise à jour
        selon la stratégie de gestion des doublons.

        Args:
            data: Liste des communes à charger

        Returns:
            Le nombre de communes chargées avec succès

        Raises:
            ValueError: Si les données ne peuvent pas être chargées
        """
        self._log_start(f"Chargement des communes en base de données (mode: {self.duplicate_handling})")

        if not data:
            self.logger.warning("Aucune commune à charger")
            return 0

        # Préparer les départements
        departments = self._prepare_departments(data)

        # Préparer les communes
        cities_to_process = self._prepare_cities(data, departments)

        # Charger les communes selon la stratégie de gestion des doublons
        try:
            if self.duplicate_handling == "skip":
                return self._process_skip_mode(cities_to_process)
            elif self.duplicate_handling == "replace":
                return self._process_replace_mode(cities_to_process)
            else:
                raise ValueError(f"Stratégie de gestion des doublons invalide: {self.duplicate_handling}")
        except Exception as e:
            self._log_error(e, "Erreur lors du chargement des communes")
            raise
