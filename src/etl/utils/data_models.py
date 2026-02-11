"""
Modèles de données intermédiaires pour le pipeline ETL.

Ce module définit les structures de données utilisées pour représenter
les informations extraites du CSV et transformées avant leur chargement
en base de données.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RegionData:
    """
    Modèle de données intermédiaire pour une région.

    Ce modèle représente une région extraite du CSV et transformée
    avant d'être chargée en base de données via RegionCreate.

    Attributes:
        name: Nom de la région (ex: "ÎLE-DE-FRANCE")
    """
    name: str

    def __str__(self) -> str:
        return f"RegionData(name='{self.name}')"


@dataclass
class DepartmentData:
    """
    Modèle de données intermédiaire pour un département.

    Ce modèle représente un département extrait du CSV et transformé
    avant d'être chargé en base de données via DepartmentCreate.

    Attributes:
        name: Nom du département (ex: "PARIS")
        code_departement: Code INSEE du département (ex: "75", "2A", "971")
        region_name: Nom de la région associée (ex: "ÎLE-DE-FRANCE")
        region_id: ID de la région en base de données (rempli après le chargement des régions)
    """
    name: str
    code_departement: str
    region_name: str
    region_id: Optional[int] = None

    def __str__(self) -> str:
        return f"DepartmentData(name='{self.name}', code_departement='{self.code_departement}', region_name='{self.region_name}')"


@dataclass
class CityData:
    """
    Modèle de données intermédiaire pour une commune.

    Ce modèle représente une commune extraite du CSV et transformée
    avant d'être chargée en base de données via CityCreate.

    Attributes:
        name: Nom de la commune (ex: "PARIS")
        code_postal: Code postal de la commune (ex: "75001")
        department_name: Nom du département (ex: "PARIS")
        latitude: Latitude GPS de la commune (optionnel)
        longitude: Longitude GPS de la commune (optionnel)
    """
    name: str
    code_postal: str
    department_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __str__(self) -> str:
        return f"CityData(name='{self.name}', code_postal='{self.code_postal}', department_name='{self.department_name}')"
