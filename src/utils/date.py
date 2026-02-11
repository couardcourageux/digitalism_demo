"""
Utilitaires pour la gestion des dates et des timestamps.

Ce module fournit des fonctions pour la manipulation des dates et des timestamps,
en utilisant systématiquement UTC pour garantir la cohérence temporelle.
"""

from datetime import datetime, timezone


def get_current_time() -> datetime:
    """
    Renvoie l'heure actuelle en UTC.
    
    Utilise datetime.now(timezone.utc) pour garantir que le timezone est
    explicitement UTC. Le datetime renvoyé est "aware" (conscient du timezone).
    
    Returns:
        datetime: Objet datetime représentant l'heure actuelle en UTC.
    
    Note:
        datetime.utcnow() est déprécié depuis Python 3.12.
        datetime.now(timezone.utc) est la méthode recommandée.
    """
    return datetime.now(timezone.utc)


def get_time_stamp(date: datetime) -> float:
    """
    Convertit un objet datetime en timestamp Unix.
    
    Args:
        date: Objet datetime à convertir. Doit être "aware" (avec timezone).
    
    Returns:
        float: Timestamp Unix (nombre de secondes depuis le 1er janvier 1970).
              La partie décimale représente les fractions de seconde.
    
    Raises:
        ValueError: Si la datetime est "naive" (sans timezone).
    
    Example:
        >>> dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        >>> get_time_stamp(dt)
        1704110400.0
    """
    if date.tzinfo is None:
        raise ValueError("La datetime doit être 'aware' (avoir un timezone)")
    return date.timestamp()
