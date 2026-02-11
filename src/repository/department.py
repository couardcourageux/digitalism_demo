from typing import List, Optional, Dict
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

    def get_by_codes(self, codes_departement: List[str]) -> Dict[str, Department]:
        """
        Récupère plusieurs départements par leurs codes.

        Args:
            codes_departement: Liste des codes départements à rechercher

        Returns:
            Dictionnaire avec les codes départements comme clés et les départements comme valeurs
        """
        if not codes_departement:
            return {}

        stmt = select(Department).where(
            Department.code_departement.in_(codes_departement),
            Department.deleted_at.is_(None)
        )
        departments = list(self.db.execute(stmt).scalars().all())
        return {dept.code_departement: dept for dept in departments}
