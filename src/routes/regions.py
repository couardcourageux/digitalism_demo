"""
Contrôleur FastAPI pour les régions.

Ce module définit tous les endpoints liés à la gestion des régions.
Il utilise le pattern Repository pour la manipulation des données.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.schemas.region import RegionCreate, RegionUpdate, RegionRead
from src.dependencies import RegionRepoDep

# Création du routeur avec un préfixe et des tags
router = APIRouter(prefix="/regions", tags=["regions"])


@router.post(
    "/",
    response_model=RegionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle région",
    description="Crée une nouvelle région avec le nom spécifié. Le nom est automatiquement converti en majuscules."
)
def create_region(
    region_in: RegionCreate,
    repo: RegionRepoDep
) -> RegionRead:
    """
    Crée une nouvelle région.
    
    Args:
        region_in: Données de la région à créer
        repo: Repository RegionRepository (injecté par dépendance)
    
    Returns:
        La région créée
    
    Raises:
        HTTPException: Si une erreur survient lors de la création
    """
    model = repo.create(region_in)
    return RegionRead.model_validate(model)


@router.get(
    "/{region_id}",
    response_model=RegionRead,
    summary="Récupérer une région par son ID",
    description="Récupère les détails d'une région spécifique à partir de son identifiant."
)
def get_region(
    region_id: int,
    repo: RegionRepoDep
) -> RegionRead:
    """
    Récupère une région par son ID.
    
    Args:
        region_id: Identifiant de la région
        repo: Repository RegionRepository (injecté par dépendance)
    
    Returns:
        La région demandée
    
    Raises:
        HTTPException: Si la région n'existe pas (404)
    """
    model = repo.get(region_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Région avec l'ID {region_id} non trouvée"
        )
    return RegionRead.model_validate(model)


@router.get(
    "/",
    response_model=List[RegionRead],
    summary="Lister toutes les régions",
    description="Récupère la liste de toutes les régions avec pagination."
)
def list_regions(
    repo: RegionRepoDep,
    skip: int = 0,
    limit: int = 100
) -> List[RegionRead]:
    """
    Liste toutes les régions.
    
    Args:
        repo: Repository RegionRepository (injecté par dépendance)
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre maximum d'éléments à retourner
    
    Returns:
        Liste des régions
    """
    models = repo.get_all(skip=skip, limit=limit)
    return [RegionRead.model_validate(m) for m in models]


@router.put(
    "/{region_id}",
    response_model=RegionRead,
    summary="Mettre à jour une région",
    description="Met à jour les informations d'une région existante. Le nom est automatiquement converti en majuscules."
)
def update_region(
    region_id: int,
    region_in: RegionUpdate,
    repo: RegionRepoDep
) -> RegionRead:
    """
    Met à jour une région.
    
    Args:
        region_id: Identifiant de la région à mettre à jour
        region_in: Données de mise à jour
        repo: Repository RegionRepository (injecté par dépendance)
    
    Returns:
        La région mise à jour
    
    Raises:
        HTTPException: Si la région n'existe pas (404)
    """
    model = repo.get(region_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Région avec l'ID {region_id} non trouvée"
        )
    updated = repo.update(model, region_in)
    return RegionRead.model_validate(updated)


@router.delete(
    "/{region_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une région",
    description="Supprime une région (soft delete). La région n'est pas supprimée de la base mais marquée comme supprimée."
)
def delete_region(
    region_id: int,
    repo: RegionRepoDep
) -> None:
    """
    Supprime une région (soft delete).
    
    Args:
        region_id: Identifiant de la région à supprimer
        repo: Repository RegionRepository (injecté par dépendance)
    
    Raises:
        HTTPException: Si la région n'existe pas (404)
    """
    if not repo.delete(region_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Région avec l'ID {region_id} non trouvée"
        )
