from pydantic import BaseModel, ConfigDict
from datetime import datetime

class BaseSchema(BaseModel):
    """Schéma de base avec configuration commune"""
    model_config = ConfigDict(
        from_attributes=True,  # Permet la conversion depuis des modèles SQLAlchemy
        str_strip_whitespace=True,  # Nettoie les espaces
        extra='forbid'  # Interdit les champs supplémentaires
    )

class TimestampedSchema(BaseSchema):
    """Schéma avec horodatage"""
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
