"""populate_regions_departments_from_json

Migration qui peuple la base de données avec les régions et départements
à partir du fichier JSON data/regions_departments.json

Revision ID: a1b2c3d4e5f6
Revises: 799f57f93b30
Create Date: 2026-02-10 21:27:00.000000

"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op
from sqlalchemy.orm import Session

# Import des helpers pour améliorer la lisibilité
import sys
from pathlib import Path as PathLib
# Ajouter le répertoire parent au path pour importer les helpers
sys.path.insert(0, str(PathLib(__file__).parent.parent))
from migration_helpers import (
    MigrationLogger,
    DataValidator,
    DatabaseOperations,
)


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '799f57f93b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Chemin vers le fichier JSON
JSON_FILE_PATH = Path(__file__).parent.parent.parent / 'data' / 'regions_departments.json'


# ============================================================================
# Fonctions auxiliaires pour la migration
# ============================================================================

def process_region(session: Session, region_data: dict) -> tuple[int, int, int]:
    """
    Traite une région et ses départements.

    Args:
        session: Session SQLAlchemy
        region_data: Données de la région

    Returns:
        Un tuple (regions_created, regions_updated, departments_created, departments_updated)
    """
    regions_created = 0
    regions_updated = 0
    departments_created = 0
    departments_updated = 0

    # Valider les données de la région
    if not DataValidator.validate_region_data(region_data):
        return (0, 0, 0, 0)

    region_name = region_data['nom']

    # Upsert de la région (insérer ou mettre à jour)
    region_id = DatabaseOperations.find_region_by_name(session, region_name)

    if region_id:
        # La région existe déjà
        MigrationLogger.logger.debug(f"Région existante trouvée: {region_name} (ID: {region_id})")
        regions_updated += 1
    else:
        # Insérer une nouvelle région
        region_id = DatabaseOperations.insert_region(session, region_name)
        MigrationLogger.logger.info(f"Nouvelle région créée: {region_name} (ID: {region_id})")
        regions_created += 1

    # Traiter les départements de cette région
    dept_stats = process_departments(session, region_data['departements'], region_id, region_name)
    departments_created += dept_stats[0]
    departments_updated += dept_stats[1]

    return (regions_created, regions_updated, departments_created, departments_updated)


def process_departments(
    session: Session,
    departments_data: list,
    region_id: int,
    region_name: str
) -> tuple[int, int]:
    """
    Traite les départements d'une région.

    Args:
        session: Session SQLAlchemy
        departments_data: Liste des données des départements
        region_id: ID de la région
        region_name: Nom de la région

    Returns:
        Un tuple (departments_created, departments_updated)
    """
    departments_created = 0
    departments_updated = 0

    for dept_data in departments_data:
        # Valider les données du département
        if not DataValidator.validate_department_data(dept_data, region_name):
            continue

        dept_code = dept_data['code']
        dept_name = dept_data['nom']

        # Upsert du département
        dept_result = process_department(session, dept_code, dept_name, region_id, region_name)
        departments_created += dept_result[0]
        departments_updated += dept_result[1]

    return (departments_created, departments_updated)


def process_department(
    session: Session,
    dept_code: str,
    dept_name: str,
    region_id: int,
    region_name: str
) -> tuple[int, int]:
    """
    Traite un département individuel (insérer ou mettre à jour).

    Args:
        session: Session SQLAlchemy
        dept_code: Code du département
        dept_name: Nom du département
        region_id: ID de la région
        region_name: Nom de la région

    Returns:
        Un tuple (created, updated) avec 1 dans la position appropriée
    """
    # Chercher le département existant
    dept = DatabaseOperations.find_department_by_code(session, dept_code)

    if dept:
        # Le département existe déjà
        dept_id, old_region_id = dept
        return update_existing_department(
            session, dept_id, dept_code, dept_name, old_region_id, region_id
        )
    else:
        # Insérer un nouveau département
        DatabaseOperations.insert_department(session, dept_name, dept_code, region_id)
        MigrationLogger.logger.info(
            f"Nouveau département créé: {dept_code} ({dept_name}) "
            f"dans région {region_name} (ID: {region_id})"
        )
        return (1, 0)


def update_existing_department(
    session: Session,
    dept_id: int,
    dept_code: str,
    dept_name: str,
    old_region_id: int,
    region_id: int
) -> tuple[int, int]:
    """
    Met à jour un département existant si nécessaire.

    Args:
        session: Session SQLAlchemy
        dept_id: ID du département
        dept_code: Code du département
        dept_name: Nouveau nom du département
        old_region_id: Ancien ID de la région
        region_id: Nouvel ID de la région

    Returns:
        Un tuple (created, updated) avec 1 dans la position appropriée
    """
    # Vérifier si la région a changé
    if old_region_id != region_id:
        DatabaseOperations.update_department(session, dept_id, dept_name, region_id)
        MigrationLogger.logger.debug(
            f"Département {dept_code} ({dept_name}) mis à jour: "
            f"région {old_region_id} -> {region_id}"
        )
        return (0, 1)

    # Vérifier si le nom a changé
    current_name = DatabaseOperations.get_department_name(session, dept_id)
    if current_name != dept_name:
        DatabaseOperations.update_department_name(session, dept_id, dept_name)
        MigrationLogger.logger.debug(
            f"Département {dept_code} nom mis à jour: {current_name} -> {dept_name}"
        )
        return (0, 1)

    return (0, 0)


def populate_database(session: Session, data: dict) -> dict:
    """
    Peuple la base de données avec les régions et départements.

    Args:
        session: Session SQLAlchemy
        data: Données JSON chargées

    Returns:
        Un dictionnaire avec les statistiques de la migration
    """
    # Compteurs pour le résumé
    stats = {
        'Régions créées': 0,
        'Régions mises à jour': 0,
        'Départements créés': 0,
        'Départements mis à jour': 0,
    }

    # Traiter chaque région
    for region_data in data['regions']:
        result = process_region(session, region_data)
        stats['Régions créées'] += result[0]
        stats['Régions mises à jour'] += result[1]
        stats['Départements créés'] += result[2]
        stats['Départements mis à jour'] += result[3]

    return stats


# ============================================================================
# Fonctions de migration Alembic
# ============================================================================

def upgrade() -> None:
    """
    Peuple la base de données avec les régions et départements à partir du JSON.

    Cette migration est idempotente: elle peut être exécutée plusieurs fois
    sans créer de doublons. Les données existantes sont mises à jour plutôt
    que recréées.
    """
    # ### commands auto generated by Alembic - please adjust! ###

    MigrationLogger.log_migration_start("population des régions et départements depuis le JSON")

    # Valider et charger le fichier JSON
    data = DataValidator.validate_json_file(JSON_FILE_PATH)
    DataValidator.validate_regions_structure(data)

    # Obtenir une connexion à la base de données
    session = DatabaseOperations.get_session()

    try:
        # Peupler la base de données
        stats = populate_database(session, data)

        # Committer la transaction
        session.commit()

        # Logging du résumé
        MigrationLogger.log_summary(stats)
        MigrationLogger.log_migration_end("population des régions et départements")

    except Exception as e:
        # Rollback en cas d'erreur
        session.rollback()
        MigrationLogger.log_error("la migration", e)
        raise
    finally:
        session.close()

    # ### end Alembic commands ###


def downgrade() -> None:
    """
    Supprime toutes les régions et départements de la base de données.

    Note: Cette opération est destructive et supprimera toutes les données
    des tables regions et departments.
    """
    # ### commands auto generated by Alembic - please adjust! ###

    MigrationLogger.log_downgrade_start("suppression des régions et départements")

    # Obtenir une connexion à la base de données
    session = DatabaseOperations.get_session()

    try:
        # Compter les éléments avant suppression
        dept_count = DatabaseOperations.count_table_rows(session, 'departments')
        region_count = DatabaseOperations.count_table_rows(session, 'regions')

        MigrationLogger.logger.info(f"Départements à supprimer: {dept_count}")
        MigrationLogger.logger.info(f"Régions à supprimer: {region_count}")

        # Supprimer tous les départements (d'abord à cause de la FK)
        DatabaseOperations.delete_all_from_table(session, 'departments')

        # Supprimer toutes les régions
        DatabaseOperations.delete_all_from_table(session, 'regions')

        session.commit()

        MigrationLogger.log_downgrade_end("suppression des régions et départements")

    except Exception as e:
        session.rollback()
        MigrationLogger.log_error("le downgrade", e)
        raise
    finally:
        session.close()

    # ### end Alembic commands ###
