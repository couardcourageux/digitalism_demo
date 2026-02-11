"""
Helpers pour les migrations Alembic.

Ce module fournit des fonctions utilitaires pour améliorer la lisibilité
et la maintenabilité des migrations, notamment en séparant les loggings
du code métier et en offrant des fonctions auxiliaires pour les opérations
répétitives.
"""
import logging
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# Configuration du logger pour les migrations
logger = logging.getLogger('alembic.env')


# ============================================================================
# Helpers de Logging
# ============================================================================

class MigrationLogger:
    """Classe helper pour centraliser les logs de migration."""
    
    # Logger statique accessible depuis les migrations
    logger = logger

    @staticmethod
    def log_migration_start(migration_name: str) -> None:
        """Log le début d'une migration."""
        logger.info(f"=== Début de la migration: {migration_name} ===")

    @staticmethod
    def log_migration_end(migration_name: str) -> None:
        """Log la fin d'une migration."""
        logger.info(f"=== Migration terminée avec succès: {migration_name} ===")

    @staticmethod
    def log_downgrade_start(migration_name: str) -> None:
        """Log le début d'un downgrade."""
        logger.info(f"=== Début du downgrade: {migration_name} ===")

    @staticmethod
    def log_downgrade_end(migration_name: str) -> None:
        """Log la fin d'un downgrade."""
        logger.info(f"=== Downgrade terminé avec succès: {migration_name} ===")

    @staticmethod
    def log_error(operation: str, error: Exception) -> None:
        """Log une erreur lors d'une opération."""
        logger.error(f"Erreur lors de {operation}: {error}")

    @staticmethod
    def log_summary(summary: Dict[str, int]) -> None:
        """Log un résumé des opérations effectuées."""
        logger.info("=== Résumé de la migration ===")
        for key, value in summary.items():
            logger.info(f"{key}: {value}")


# ============================================================================
# Helpers de Validation de Données
# ============================================================================

class DataValidator:
    """Classe helper pour valider les données avant insertion."""

    @staticmethod
    def validate_json_file(file_path: Path) -> Dict[str, Any]:
        """
        Valide et charge un fichier JSON.

        Args:
            file_path: Chemin vers le fichier JSON

        Returns:
            Les données JSON chargées

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le JSON est invalide ou mal structuré
        """
        if not file_path.exists():
            raise FileNotFoundError(
                f"Le fichier JSON n'existe pas: {file_path}. "
                "Veuillez exécuter le script ETL pour le générer."
            )

        logger.info(f"Lecture du fichier JSON: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Le fichier JSON n'est pas valide: {e}")

        return data

    @staticmethod
    def validate_regions_structure(data: Dict[str, Any]) -> None:
        """
        Valide la structure des données de régions.

        Args:
            data: Données JSON à valider

        Raises:
            ValueError: Si la structure est invalide
        """
        if 'regions' not in data:
            raise ValueError("Le JSON doit contenir une clé 'regions'")

        if not isinstance(data['regions'], list):
            raise ValueError("La clé 'regions' doit être une liste")

        logger.info(f"Nombre de régions à traiter: {len(data['regions'])}")

    @staticmethod
    def validate_region_data(region_data: Dict[str, Any]) -> bool:
        """
        Valide les données d'une région.

        Args:
            region_data: Données de la région

        Returns:
            True si les données sont valides, False sinon
        """
        if 'nom' not in region_data:
            logger.warning("Région sans 'nom' détectée, ignorée")
            return False

        if 'departements' not in region_data:
            logger.warning(f"Région {region_data['nom']} sans 'departements', ignorée")
            return False

        if not isinstance(region_data['departements'], list):
            logger.warning(
                f"La clé 'departements' de {region_data['nom']} doit être une liste"
            )
            return False

        return True

    @staticmethod
    def validate_department_data(dept_data: Dict[str, Any], region_name: str) -> bool:
        """
        Valide les données d'un département.

        Args:
            dept_data: Données du département
            region_name: Nom de la région parente

        Returns:
            True si les données sont valides, False sinon
        """
        if 'code' not in dept_data or 'nom' not in dept_data:
            logger.warning(
                f"Département sans 'code' ou 'nom' détecté dans {region_name}, ignoré"
            )
            return False

        return True


# ============================================================================
# Helpers d'Opérations de Base de Données
# ============================================================================

class DatabaseOperations:
    """Classe helper pour les opérations de base de données courantes."""

    @staticmethod
    def get_session() -> Session:
        """
        Crée et retourne une session SQLAlchemy.

        Returns:
            Une session SQLAlchemy
        """
        bind = op.get_bind()
        return Session(bind=bind)

    @staticmethod
    def find_region_by_name(session: Session, name: str) -> Optional[int]:
        """
        Trouve une région par son nom.

        Args:
            session: Session SQLAlchemy
            name: Nom de la région

        Returns:
            L'ID de la région si trouvée, None sinon
        """
        result = session.execute(
            sa.text("SELECT id FROM regions WHERE name = :name"),
            {'name': name}
        ).fetchone()
        return result[0] if result else None

    @staticmethod
    def insert_region(session: Session, name: str) -> int:
        """
        Insère une nouvelle région.

        Args:
            session: Session SQLAlchemy
            name: Nom de la région

        Returns:
            L'ID de la région créée
        """
        result = session.execute(
            sa.text("""
                INSERT INTO regions (name, created_at, updated_at)
                VALUES (:name, NOW(), NOW())
                RETURNING id
            """),
            {'name': name}
        )
        return result.fetchone()[0]

    @staticmethod
    def find_department_by_code(session: Session, code: str) -> Optional[Tuple[int, int]]:
        """
        Trouve un département par son code.

        Args:
            session: Session SQLAlchemy
            code: Code du département

        Returns:
            Un tuple (id, region_id) si trouvé, None sinon
        """
        result = session.execute(
            sa.text("SELECT id, region_id FROM departments WHERE code_departement = :code"),
            {'code': code}
        ).fetchone()
        return result if result else None

    @staticmethod
    def insert_department(
        session: Session,
        name: str,
        code: str,
        region_id: int
    ) -> None:
        """
        Insère un nouveau département.

        Args:
            session: Session SQLAlchemy
            name: Nom du département
            code: Code du département
            region_id: ID de la région
        """
        session.execute(
            sa.text("""
                INSERT INTO departments (name, code_departement, region_id, created_at, updated_at)
                VALUES (:name, :code, :region_id, NOW(), NOW())
            """),
            {'name': name, 'code': code, 'region_id': region_id}
        )

    @staticmethod
    def update_department(
        session: Session,
        dept_id: int,
        name: str,
        region_id: int
    ) -> None:
        """
        Met à jour un département.

        Args:
            session: Session SQLAlchemy
            dept_id: ID du département
            name: Nouveau nom du département
            region_id: Nouvel ID de la région
        """
        session.execute(
            sa.text("""
                UPDATE departments
                SET name = :name, region_id = :region_id, updated_at = NOW()
                WHERE id = :id
            """),
            {'name': name, 'region_id': region_id, 'id': dept_id}
        )

    @staticmethod
    def update_department_name(session: Session, dept_id: int, name: str) -> None:
        """
        Met à jour uniquement le nom d'un département.

        Args:
            session: Session SQLAlchemy
            dept_id: ID du département
            name: Nouveau nom du département
        """
        session.execute(
            sa.text("""
                UPDATE departments
                SET name = :name, updated_at = NOW()
                WHERE id = :id
            """),
            {'name': name, 'id': dept_id}
        )

    @staticmethod
    def get_department_name(session: Session, dept_id: int) -> str:
        """
        Récupère le nom d'un département.

        Args:
            session: Session SQLAlchemy
            dept_id: ID du département

        Returns:
            Le nom du département
        """
        result = session.execute(
            sa.text("SELECT name FROM departments WHERE id = :id"),
            {'id': dept_id}
        ).fetchone()
        return result[0] if result else ""

    @staticmethod
    def count_table_rows(session: Session, table_name: str) -> int:
        """
        Compte le nombre de lignes dans une table.

        Args:
            session: Session SQLAlchemy
            table_name: Nom de la table

        Returns:
            Le nombre de lignes
        """
        result = session.execute(
            sa.text(f"SELECT COUNT(*) FROM {table_name}")
        ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def delete_all_from_table(session: Session, table_name: str) -> None:
        """
        Supprime toutes les lignes d'une table.

        Args:
            session: Session SQLAlchemy
            table_name: Nom de la table
        """
        session.execute(sa.text(f"DELETE FROM {table_name}"))


# ============================================================================
# Helpers de Gestion de Transactions
# ============================================================================

class TransactionManager:
    """Classe helper pour gérer les transactions de base de données."""

    @staticmethod
    def execute_in_transaction(
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ) -> Any:
        """
        Exécute une opération dans une transaction avec gestion des erreurs.

        Args:
            operation_name: Nom de l'opération pour les logs
            operation_func: Fonction à exécuter
            *args: Arguments positionnels pour la fonction
            **kwargs: Arguments nommés pour la fonction

        Returns:
            Le résultat de l'opération

        Raises:
            Exception: Si une erreur survient pendant l'opération
        """
        session = DatabaseOperations.get_session()
        try:
            result = operation_func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            MigrationLogger.log_error(operation_name, e)
            raise
        finally:
            session.close()
