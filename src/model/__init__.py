"""
Modèles SQLAlchemy pour l'application Digitalism FastAPI.

Ce package contient les modèles de données pour :
- Region : Régions administratives françaises
- Department : Départements français
- City : Villes françaises

Tous les modèles héritent de Base qui fournit :
- id : Identifiant unique
- created_at : Date de création
- updated_at : Date de dernière mise à jour
- deleted_at : Date de suppression logique (soft delete)
"""

from src.model.base import Base
from src.model.region import Region
from src.model.department import Department
from src.model.city import City

__all__ = ["Base", "Region", "Department", "City"]
