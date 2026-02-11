from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import field_validator



class DigitalismSettings(BaseSettings):
    DATABASE_URL: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str

    CSV_DATA_PATH: str = "data/csv"

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must be a valid PostgreSQL URL')
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return DigitalismSettings()