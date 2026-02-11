"""
Scripts ETL pour le projet Digitalism FastAPI.

Ce package contient les scripts principaux pour exécuter les pipelines ETL.
"""

from src.etl.scripts.city_etl_pipeline import run_city_etl_pipeline

__all__ = ["run_city_etl_pipeline"]
