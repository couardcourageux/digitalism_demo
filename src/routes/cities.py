"""
Contrôleur FastAPI pour les communes (villes).

Ce module définit tous les endpoints liés à la gestion des communes.
Il utilise le pattern Repository pour la manipulation des données.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.schemas.city import CityCreate, CityUpdate, CityRead
from src.dependencies import CityRepoDep, DepartmentRepoDep
from src.model.city import City

# Création du routeur avec un préfixe et des tags
router = APIRouter(prefix="/cities", tags=["cities"])


@router.post(
    "/",
    response_model=CityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle commune",
    description="Crée une nouvelle commune avec le nom et le code postal spécifiés. Le nom est automatiquement converti en majuscules et le département est déduit du code postal."
)
def create_city(
    city_in: CityCreate,
    repo: CityRepoDep,
    department_repo: DepartmentRepoDep
) -> CityRead:
    """
    Crée une nouvelle commune.

    Args:
        city_in: Données de la commune à créer
        repo: Repository CityRepository (injecté par dépendance)
        department_repo: Repository DepartmentRepository (injecté par dépendance)

    Returns:
        La commune créée

    Raises:
        HTTPException: Si une erreur survient lors de la création
    """
    # Extraire le code département depuis le code postal
    code_departement = City.calculate_department_from_postal_code(city_in.code_postal)
    
    # Récupérer le département correspondant
    department = department_repo.get_by_code(code_departement)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec le code '{code_departement}' non trouvé"
        )
    
    # Ajouter department_id aux données de création
    city_data = city_in.model_dump()
    city_data['department_id'] = department.id
    
    model = repo.create(city_data)
    return CityRead.model_validate(model)


@router.post(
    "/upsert",
    response_model=CityRead,
    summary="Créer ou mettre à jour une commune (upsert)",
    description="Récupère une commune existante par son nom et code postal, ou la crée si elle n'existe pas. Le département est déduit du code postal."
)
def upsert_city(
    city_in: CityCreate,
    repo: CityRepoDep,
    department_repo: DepartmentRepoDep
) -> CityRead:
    """
    Crée ou met à jour une commune (upsert).

    Args:
        city_in: Données de la commune
        repo: Repository CityRepository (injecté par dépendance)
        department_repo: Repository DepartmentRepository (injecté par dépendance)

    Returns:
        La commune existante ou nouvellement créée
    """
    # Extraire le code département depuis le code postal
    code_departement = City.calculate_department_from_postal_code(city_in.code_postal)
    
    # Récupérer le département correspondant
    department = department_repo.get_by_code(code_departement)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec le code '{code_departement}' non trouvé"
        )
    
    # Ajouter department_id aux données de création
    city_data = city_in.model_dump()
    city_data['department_id'] = department.id
    
    model = repo.get_or_create(city_data)
    return CityRead.model_validate(model)


@router.post(
    "/bulk",
    response_model=List[CityRead],
    status_code=status.HTTP_201_CREATED,
    summary="Créer plusieurs communes en une seule requête",
    description="Crée plusieurs communes en une seule requête pour optimiser les performances. Le département est déduit du code postal pour chaque commune."
)
def bulk_create_cities(
    cities_in: List[CityCreate],
    repo: CityRepoDep,
    department_repo: DepartmentRepoDep
) -> List[CityRead]:
    """
    Crée plusieurs communes en une seule requête.

    Args:
        cities_in: Liste des données de communes à créer
        repo: Repository CityRepository (injecté par dépendance)
        department_repo: Repository DepartmentRepository (injecté par dépendance)

    Returns:
        Liste des communes créées
    """
    # Cache pour éviter les requêtes répétées sur les mêmes codes département
    department_cache = {}
    
    # Préparer les données avec department_id
    cities_data = []
    for city_in in cities_in:
        # Extraire le code département depuis le code postal
        code_departement = City.calculate_department_from_postal_code(city_in.code_postal)
        
        # Récupérer le département depuis le cache ou via repository
        if code_departement not in department_cache:
            department = department_repo.get_by_code(code_departement)
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Département avec le code '{code_departement}' non trouvé"
                )
            department_cache[code_departement] = department
        
        # Ajouter department_id aux données de création
        city_data = city_in.model_dump()
        city_data['department_id'] = department_cache[code_departement].id
        cities_data.append(city_data)
    
    models = repo.bulk_create(cities_data)
    return [CityRead.model_validate(m) for m in models]


@router.get(
    "/{city_id}",
    response_model=CityRead,
    summary="Récupérer une commune par son ID",
    description="Récupère les détails d'une commune spécifique à partir de son identifiant."
)
def get_city(
    city_id: int,
    repo: CityRepoDep
) -> CityRead:
    """
    Récupère une commune par son ID.

    Args:
        city_id: Identifiant de la commune
        repo: Repository CityRepository (injecté par dépendance)

    Returns:
        La commune demandée

    Raises:
        HTTPException: Si la commune n'existe pas (404)
    """
    model = repo.get(city_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {city_id} non trouvée"
        )
    return CityRead.model_validate(model)


@router.get(
    "/by-name/{name}",
    response_model=CityRead,
    summary="Récupérer une commune par son nom",
    description="Récupère une commune correspondant au nom spécifié (insensible à la casse)."
)
def get_city_by_name(
    name: str,
    repo: CityRepoDep
) -> CityRead:
    """
    Récupère une commune par son nom.

    Args:
        name: Nom de la commune (insensible à la casse)
        repo: Repository CityRepository (injecté par dépendance)

    Returns:
        La commune correspondante

    Raises:
        HTTPException: Si la commune n'existe pas (404)
    """
    model = repo.get_by_name(name)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec le nom '{name}' non trouvée"
        )
    return CityRead.model_validate(model)


@router.get(
    "/by-postal-code/{code_postal}",
    response_model=List[CityRead],
    summary="Récupérer des communes par code postal",
    description="Récupère la liste de toutes les communes correspondant au code postal spécifié."
)
def get_cities_by_postal_code(
    code_postal: str,
    repo: CityRepoDep
) -> List[CityRead]:
    """
    Récupère des communes par code postal.

    Args:
        code_postal: Code postal (5 chiffres)
        repo: Repository CityRepository (injecté par dépendance)

    Returns:
        Liste des communes correspondantes
    """
    models = repo.get_by_postal_code(code_postal)
    return [CityRead.model_validate(m) for m in models]


@router.get(
    "/by-department/{department_id}",
    response_model=List[CityRead],
    summary="Récupérer les communes d'un département",
    description="Récupère la liste de toutes les communes appartenant à un département spécifique."
)
def get_cities_by_department(
    department_id: int,
    repo: CityRepoDep
) -> List[CityRead]:
    """
    Récupère les communes d'un département.

    Args:
        department_id: Identifiant du département
        repo: Repository CityRepository (injecté par dépendance)

    Returns:
        Liste des communes du département
    """
    models = repo.get_by_department(department_id)
    return [CityRead.model_validate(m) for m in models]


@router.get(
    "/",
    response_model=List[CityRead],
    summary="Lister toutes les communes",
    description="Récupère la liste de toutes les communes avec pagination."
)
def list_cities(
    repo: CityRepoDep,
    skip: int = 0,
    limit: int = 100
) -> List[CityRead]:
    """
    Liste toutes les communes.

    Args:
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre maximum d'éléments à retourner
        repo: Repository CityRepository (injecté par dépendance)

    Returns:
        Liste des communes
    """
    models = repo.get_all(skip=skip, limit=limit)
    return [CityRead.model_validate(m) for m in models]


@router.put(
    "/{city_id}",
    response_model=CityRead,
    summary="Mettre à jour une commune",
    description="Met à jour les informations d'une commune existante. Le nom est automatiquement converti en majuscules et le département est déduit du code postal si celui-ci est fourni."
)
def update_city(
    city_id: int,
    city_in: CityUpdate,
    repo: CityRepoDep,
    department_repo: DepartmentRepoDep
) -> CityRead:
    """
    Met à jour une commune.

    Args:
        city_id: Identifiant de la commune à mettre à jour
        city_in: Données de mise à jour
        repo: Repository CityRepository (injecté par dépendance)
        department_repo: Repository DepartmentRepository (injecté par dépendance)

    Returns:
        La commune mise à jour

    Raises:
        HTTPException: Si la commune n'existe pas (404)
    """
    model = repo.get(city_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {city_id} non trouvée"
        )
    
    # Si le code_postal est fourni, mettre à jour le department_id
    if city_in.code_postal is not None:
        # Extraire le code département depuis le code postal
        code_departement = City.calculate_department_from_postal_code(city_in.code_postal)
        
        # Récupérer le département correspondant
        department = department_repo.get_by_code(code_departement)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Département avec le code '{code_departement}' non trouvé"
            )
        
        # Ajouter department_id aux données de mise à jour
        city_data = city_in.model_dump(exclude_none=True)
        city_data['department_id'] = department.id
    else:
        city_data = city_in.model_dump(exclude_none=True)
    
    updated = repo.update(model, city_data)
    return CityRead.model_validate(updated)


@router.delete(
    "/{city_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une commune",
    description="Supprime une commune (soft delete). La commune n'est pas supprimée de la base mais marquée comme supprimée."
)
def delete_city(
    city_id: int,
    repo: CityRepoDep
) -> None:
    """
    Supprime une commune (soft delete).

    Args:
        city_id: Identifiant de la commune à supprimer
        repo: Repository CityRepository (injecté par dépendance)

    Raises:
        HTTPException: Si la commune n'existe pas (404)
    """
    if not repo.delete(city_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commune avec l'ID {city_id} non trouvée"
        )
