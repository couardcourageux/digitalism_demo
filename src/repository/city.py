"""Repository pour City."""

from typing import List, Optional, Union, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.model.city import City
from src.model.department import Department
from src.schemas.city import CityCreate, CityUpdate
from src.repository.base import BaseRepository


class CityRepository(BaseRepository[City, CityCreate, CityUpdate]):
    def __init__(self, db: Session):
        super().__init__(City, db)

    def get_by_name(self, name: str) -> Optional[City]:
        """
        Récupère une ville par son nom.

        Args:
            name: Nom de la ville (insensible à la casse)

        Returns:
            La ville trouvée ou None
        """
        stmt = select(City).where(
            City.name == name.upper(),
            City.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_postal_code(self, code_postal: str) -> List[City]:
        """
        Récupère toutes les villes d'un code postal.

        Args:
            code_postal: Code postal (5 chiffres)

        Returns:
            Liste des villes trouvées
        """
        stmt = select(City).where(
            City.code_postal == code_postal,
            City.deleted_at.is_(None)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_department(self, department_id: int) -> List[City]:
        """
        Récupère toutes les villes d'un département.

        Args:
            department_id: Identifiant du département

        Returns:
            Liste des villes du département
        """
        stmt = select(City).where(
            City.department_id == department_id,
            City.deleted_at.is_(None)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_name_and_postal_code(self, name: str, code_postal: str) -> Optional[City]:
        """
        Récupère une ville par son nom et son code postal.

        Args:
            name: Nom de la ville (insensible à la casse)
            code_postal: Code postal (5 chiffres)

        Returns:
            La ville trouvée ou None
        """
        stmt = select(City).where(
            City.name == name.upper(),
            City.code_postal == code_postal,
            City.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_or_create(self, city_in: Union[CityCreate, Dict[str, Any]]) -> City:
        """
        Récupère une ville existante ou la crée si elle n'existe pas (upsert).

        Args:
            city_in: Données de la ville (objet Pydantic ou dictionnaire)

        Returns:
            La ville existante ou nouvellement créée
        """
        # Extraire name et code_postal depuis l'objet Pydantic ou le dictionnaire
        if isinstance(city_in, dict):
            name = city_in.get('name')
            code_postal = city_in.get('code_postal')
        else:
            name = city_in.name
            code_postal = city_in.code_postal
        
        existing = self.get_by_name_and_postal_code(name, code_postal)
        if existing:
            return existing
        return self.create(city_in)

    def create(self, obj_in: Union[CityCreate, Dict[str, Any]]) -> City:
        """
        Crée une ville.
        
        Si department_id est déjà présent dans les données (dictionnaire), il est utilisé directement.
        Sinon, le département est déduit automatiquement à partir du code postal.

        Args:
            obj_in: Données de la ville (objet Pydantic ou dictionnaire)

        Returns:
            La ville créée
        """
        # Extraire les données sous forme de dictionnaire
        if isinstance(obj_in, dict):
            city_data = obj_in.copy()
        else:
            city_data = obj_in.model_dump()
        
        # Si department_id n'est pas déjà présent, le déduire du code postal
        if 'department_id' not in city_data:
            code_departement = City.calculate_department_from_postal_code(city_data['code_postal'])
            
            # Récupérer le département correspondant
            stmt = select(Department).where(
                Department.code_departement == code_departement,
                Department.deleted_at.is_(None)
            )
            department = self.db.execute(stmt).scalar_one_or_none()
            
            if department is None:
                raise ValueError(f"Département non trouvé pour le code postal {city_data['code_postal']} (code département: {code_departement})")
            
            city_data['department_id'] = department.id
        
        # Créer la ville avec les données fournies
        db_obj = self.model(**city_data)
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def bulk_create(self, cities_in: List[Union[CityCreate, Dict[str, Any]]]) -> List[City]:
        """
        Crée plusieurs villes en une seule requête.
        
        Si department_id est déjà présent dans les données (dictionnaire), il est utilisé directement.
        Sinon, le département est déduit automatiquement à partir du code postal.

        Args:
            cities_in: Liste des données de villes à créer (objets Pydantic ou dictionnaires)

        Returns:
            Liste des villes créées
        """
        # Séparer les villes qui ont déjà un department_id de celles qui n'en ont pas
        cities_with_dept = []
        cities_without_dept = []
        
        for city_in in cities_in:
            # Extraire les données sous forme de dictionnaire
            if isinstance(city_in, dict):
                city_data = city_in
            else:
                city_data = city_in.model_dump()
            
            if 'department_id' in city_data:
                cities_with_dept.append(city_data)
            else:
                cities_without_dept.append(city_data)
        
        # Récupérer tous les codes départements uniques nécessaires pour les villes sans department_id
        code_departements = set()
        for city_data in cities_without_dept:
            code_departement = City.calculate_department_from_postal_code(city_data['code_postal'])
            code_departements.add(code_departement)
        
        # Récupérer tous les départements nécessaires en une seule requête
        departments = {}
        if code_departements:
            stmt = select(Department).where(
                Department.code_departement.in_(code_departements),
                Department.deleted_at.is_(None)
            )
            departments = {dept.code_departement: dept for dept in self.db.execute(stmt).scalars().all()}
            
            # Vérifier que tous les départements existent
            missing_departments = code_departements - set(departments.keys())
            if missing_departments:
                raise ValueError(f"Départements non trouvés: {', '.join(missing_departments)}")
        
        # Créer les villes avec les department_id déduits ou fournis
        db_objs = []
        
        # Traiter les villes avec department_id déjà fourni
        for city_data in cities_with_dept:
            db_objs.append(self.model(**city_data))
        
        # Traiter les villes sans department_id (déduction automatique)
        for city_data in cities_without_dept:
            code_departement = City.calculate_department_from_postal_code(city_data['code_postal'])
            city_data['department_id'] = departments[code_departement].id
            db_objs.append(self.model(**city_data))
        
        self.db.add_all(db_objs)
        self.db.flush()
        for obj in db_objs:
            self.db.refresh(obj)
        return db_objs
