from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.model.region import Region
from src.schemas.region import RegionCreate, RegionUpdate
from src.repository.base import BaseRepository

class RegionRepository(BaseRepository[Region, RegionCreate, RegionUpdate]):
    def __init__(self, db: Session):
        super().__init__(Region, db)

    def get_by_name(self, name: str) -> Optional[Region]:
        """
        Récupère une région par son nom.

        Args:
            name: Nom de la région à rechercher

        Returns:
            La région si trouvée, None sinon
        """
        stmt = select(Region).where(Region.name == name)
        return self.db.execute(stmt).scalar_one_or_none()
