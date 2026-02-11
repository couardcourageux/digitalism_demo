from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.model.department import Department
from src.schemas.department import DepartmentCreate, DepartmentUpdate
from src.repository.base import BaseRepository

class DepartmentRepository(BaseRepository[Department, DepartmentCreate, DepartmentUpdate]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_region(self, region_id: int) -> List[Department]:
        """Récupère tous les départements d'une région"""
        stmt = select(Department).where(
            Department.region_id == region_id,
            Department.deleted_at.is_(None)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_code(self, code_departement: str) -> Optional[Department]:
        """Récupère un département par son code"""
        stmt = select(Department).where(
            Department.code_departement == code_departement,
            Department.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalar_one_or_none()
