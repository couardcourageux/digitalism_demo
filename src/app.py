from datetime import datetime, timezone

from fastapi import FastAPI

from src.config import get_settings
from src.routes.regions import router as regions_router
from src.routes.departments import router as departments_router
from src.routes.cities import router as cities_router

# Import des modèles pour garantir qu'ils sont enregistrés dans le registre de SQLAlchemy
from src.model import Base, Region, Department, City

app = FastAPI(
    title="Digitalism API",
    description="API pour la gestion des régions, départements et communes françaises",
    version="1.0.0"
)

# Inclusion des routeurs
app.include_router(regions_router)
app.include_router(departments_router)
app.include_router(cities_router)


@app.get("/")
def read_root():
    return {
        "message": "Bienvenue sur l'API Digitalism",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """
    Vérifie la santé de l'application.
    
    Returns:
        dict: Statut de l'application avec timestamp UTC.
    
    Cet endpoint peut être utilisé par les orchestrateurs de conteneurs
    ou les load balancers pour vérifier que l'application fonctionne.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "digitalism-fastapi"
    }