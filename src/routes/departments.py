"""
Contrôleur FastAPI pour les départements.

Ce module définit tous les endpoints liés à la gestion des départements.
Il utilise le pattern Repository pour la manipulation des données.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentRead
from src.dependencies import DepartmentRepoDep

# Création du routeur avec un préfixe et des tags
router = APIRouter(prefix="/departments", tags=["departments"])


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau département",
    description="Crée un nouveau département avec le nom et l'ID de région spécifiés. Le nom est automatiquement converti en majuscules."
)
def create_department(
    department_in: DepartmentCreate,
    repo: DepartmentRepoDep
) -> DepartmentRead:
    """
    Crée un nouveau département.
    
    Args:
        department_in: Données du département à créer
        repo: Repository DepartmentRepository (injecté par dépendance)
    
    Returns:
        Le département créé
    
    Raises:
        HTTPException: Si une erreur survient lors de la création
    """
    model = repo.create(department_in)
    return DepartmentRead.model_validate(model)


@router.get(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Récupérer un département par son ID",
    description="Récupère les détails d'un département spécifique à partir de son identifiant."
)
def get_department(
    department_id: int,
    repo: DepartmentRepoDep
) -> DepartmentRead:
    """
    Récupère un département par son ID.
    
    Args:
        department_id: Identifiant du département
        repo: Repository DepartmentRepository (injecté par dépendance)
    
    Returns:
        Le département demandé
    
    Raises:
        HTTPException: Si le département n'existe pas (404)
    """
    model = repo.get(department_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec l'ID {department_id} non trouvé"
        )
    return DepartmentRead.model_validate(model)


@router.get(
    "/",
    response_model=List[DepartmentRead],
    summary="Lister tous les départements",
    description="Récupère la liste de tous les départements avec pagination."
)
def list_departments(
    repo: DepartmentRepoDep,
    skip: int = 0,
    limit: int = 100
) -> List[DepartmentRead]:
    """
    Liste tous les départements.
    
    Args:
        repo: Repository DepartmentRepository (injecté par dépendance)
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre maximum d'éléments à retourner
    
    Returns:
        Liste des départements
    """
    models = repo.get_all(skip=skip, limit=limit)
    return [DepartmentRead.model_validate(m) for m in models]


@router.put(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Mettre à jour un département",
    description="Met à jour les informations d'un département existant. Le nom est automatiquement converti en majuscules."
)
def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    repo: DepartmentRepoDep
) -> DepartmentRead:
    """
    Met à jour un département.
    
    Args:
        department_id: Identifiant du département à mettre à jour
        department_in: Données de mise à jour
        repo: Repository DepartmentRepository (injecté par dépendance)
    
    Returns:
        Le département mis à jour
    
    Raises:
        HTTPException: Si le département n'existe pas (404)
    """
    model = repo.get(department_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec l'ID {department_id} non trouvé"
        )
    updated = repo.update(model, department_in)
    return DepartmentRead.model_validate(updated)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un département",
    description="Supprime un département (soft delete). Le département n'est pas supprimé de la base mais marqué comme supprimé."
)
def delete_department(
    department_id: int,
    repo: DepartmentRepoDep
) -> None:
    """
    Supprime un département (soft delete).
    
    Args:
        department_id: Identifiant du département à supprimer
        repo: Repository DepartmentRepository (injecté par dépendance)
    
    Raises:
        HTTPException: Si le département n'existe pas (404)
    """
    if not repo.delete(department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Département avec l'ID {department_id} non trouvé"
        )


@router.get(
    "/by-region/{region_id}",
    response_model=List[DepartmentRead],
    summary="Lister les départements d'une région",
    description="Récupère la liste de tous les départements appartenant à une région spécifique."
)
def list_departments_by_region(
    region_id: int,
    repo: DepartmentRepoDep
) -> List[DepartmentRead]:
    """
    Liste les départements d'une région.

    Args:
        region_id: Identifiant de la région
        repo: Repository DepartmentRepository (injecté par dépendance)

    Returns:
        Liste des départements de la région
    """
    models = repo.get_by_region(region_id)
    return [DepartmentRead.model_validate(m) for m in models]
