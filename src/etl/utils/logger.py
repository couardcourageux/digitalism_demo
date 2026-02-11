"""
Module de logging pour les opérations ETL.

Ce module fournit un logger configuré spécifiquement pour les opérations ETL,
permettant de tracer les étapes d'extraction, transformation et chargement.
"""

import logging
from src.etl.config import LOG_LEVEL, LOG_FORMAT


def get_etl_logger(name: str = "etl") -> logging.Logger:
    """
    Crée et configure un logger pour les opérations ETL.

    Args:
        name: Nom du logger (par défaut: "etl")

    Returns:
        Logger configuré avec le niveau et le format définis dans la configuration.
    """
    logger = logging.getLogger(name)
    
    # Éviter d'ajouter plusieurs handlers si le logger est déjà configuré
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    return logger
