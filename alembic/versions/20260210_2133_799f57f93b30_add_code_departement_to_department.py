"""add_code_departement_to_department

Ajoute le champ code_departement à la table departments et modifie la table cities.

Modifications apportées :
- departments : Ajout du champ code_departement (String(3), nullable=False)
  Ce champ contient le code INSEE du département (ex: "01", "2A", "75", "971")
  Création de l'index idx_department_code et de la contrainte unique uq_department_code

- cities : Modification du champ name (VARCHAR(100) → VARCHAR(255))
  Ajout du champ code_postal (String(5), nullable=False)
  Création des index idx_city_name, idx_city_department_id, idx_city_code_postal
  Création de la contrainte unique uq_city_name_code_postal

Revision ID: 799f57f93b30
Revises: 06d3a879a5a1
Create Date: 2026-02-10 21:33:45.929622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799f57f93b30'
down_revision: Union[str, None] = '06d3a879a5a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================================
# Fonctions auxiliaires pour la modification de la table cities
# ============================================================================

def add_cities_modifications() -> None:
    """
    Applique les modifications à la table cities.

    Modifications :
    - Ajout du champ code_postal (String(5), nullable=False)
    - Extension du champ name de VARCHAR(100) à VARCHAR(255)
    - Création des index idx_city_code_postal, idx_city_name
    - Note: idx_city_department_id est déjà créé par initial_migration
    - Création de la contrainte unique uq_city_name_code_postal
    """
    op.add_column('cities', sa.Column('code_postal', sa.String(length=5), nullable=False))

    op.alter_column(
        'cities',
        'name',
        existing_type=sa.VARCHAR(length=100),
        type_=sa.String(length=255),
        existing_nullable=False
    )

    op.create_index('idx_city_code_postal', 'cities', ['code_postal'], unique=False)
    op.create_index('idx_city_name', 'cities', ['name'], unique=False)

    op.create_unique_constraint('uq_city_name_code_postal', 'cities', ['name', 'code_postal'])


def remove_cities_modifications() -> None:
    """
    Annule les modifications de la table cities.

    Opérations effectuées dans l'ordre inverse de l'upgrade :
    - Suppression de la contrainte unique uq_city_name_code_postal
    - Suppression des index idx_city_name, idx_city_code_postal
    - Note: idx_city_department_id est supprimé par initial_migration
    - Réduction du champ name de VARCHAR(255) à VARCHAR(100)
    - Suppression du champ code_postal
    """
    op.drop_constraint('uq_city_name_code_postal', 'cities', type_='unique')
    op.drop_index('idx_city_name', table_name='cities')
    op.drop_index('idx_city_code_postal', table_name='cities')

    op.alter_column(
        'cities',
        'name',
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=100),
        existing_nullable=False
    )

    op.drop_column('cities', 'code_postal')


# ============================================================================
# Fonctions auxiliaires pour la modification de la table departments
# ============================================================================

def add_departments_modifications() -> None:
    """
    Applique les modifications à la table departments.

    Modifications :
    - Ajout du champ code_departement (String(3), nullable=False)
      Ce champ contient le code INSEE du département (ex: "01", "2A", "75", "971")
    - Création de l'index idx_department_code pour optimiser les recherches par code
    - Création de la contrainte unique uq_department_code pour garantir l'unicité des codes
    """
    op.add_column('departments', sa.Column('code_departement', sa.String(length=3), nullable=False))
    op.create_index('idx_department_code', 'departments', ['code_departement'], unique=False)
    op.create_unique_constraint('uq_department_code', 'departments', ['code_departement'])


def remove_departments_modifications() -> None:
    """
    Annule les modifications de la table departments.

    Opérations effectuées dans l'ordre inverse de l'upgrade :
    - Suppression de la contrainte unique uq_department_code
    - Suppression de l'index idx_department_code
    - Suppression du champ code_departement
    """
    op.drop_constraint('uq_department_code', 'departments', type_='unique')
    op.drop_index('idx_department_code', table_name='departments')
    op.drop_column('departments', 'code_departement')


# ============================================================================
# Fonctions de migration Alembic
# ============================================================================

def upgrade() -> None:
    """
    Applique toutes les modifications de schéma.

    Ordre des opérations :
    1. Modifications de la table cities
    2. Modifications de la table departments
    """
    # ### commands auto generated by Alembic - please adjust! ###

    # Modifications pour la table cities
    add_cities_modifications()

    # Modifications pour la table departments
    add_departments_modifications()

    # ### end Alembic commands ###


def downgrade() -> None:
    """
    Annule toutes les modifications de schéma.

    Ordre des opérations (inverse de l'upgrade) :
    1. Rollback des modifications de la table departments
    2. Rollback des modifications de la table cities
    """
    # ### commands auto generated by Alembic - please adjust! ###

    # Rollback des modifications pour la table departments
    remove_departments_modifications()

    # Rollback des modifications pour la table cities
    remove_cities_modifications()

    # ### end Alembic commands ###
