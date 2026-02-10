from pydantic_settings import BaseSettings
from functools import lru_cache



class DigitalismSettings(BaseSettings):
    DATABASE_URL: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str

    CSV_DATA_PATH: str = "data/csv"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return DigitalismSettings()