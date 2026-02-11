from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from src.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Vérifie les connexions avant utilisation
    pool_recycle=3600,   # Recycle les connexions après 1 heure
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Générateur de session de base de données pour FastAPI.
    
    Yields:
        Session: Session SQLAlchemy active.
    
    Le commit est automatique en cas de succès, rollback en cas d'erreur,
    et la session est toujours fermée dans le bloc finally.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
