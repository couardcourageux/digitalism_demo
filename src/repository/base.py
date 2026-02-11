from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.model.base import Base
from src.schemas.base import BaseSchema
from src.utils.date import get_current_time


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseSchema)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """Récupère un modèle par son ID"""
        stmt = select(self.model).where(self.model.id == id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Récupère tous les modèles non supprimés avec pagination"""
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None)
        ).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Crée un modèle à partir d'un schéma de création"""
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Met à jour un modèle à partir d'un schéma de mise à jour"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """Supprime logiquement un modèle (soft delete)"""
        obj = self.get(id)
        if obj:
            obj.deleted_at = get_current_time()
            self.db.flush()
            return True
        return False
