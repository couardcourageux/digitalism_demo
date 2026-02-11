from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path Python
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importer les modèles et la configuration
from src.config import get_settings
from src.database import engine
from src.model import Base

# this is the Alembic Config object
config = context.config

# Interpréter le fichier de configuration pour Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ajouter l'URL de la base de données depuis les settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Ajouter les attributs de votre modèle pour autogenerate support
target_metadata = Base.metadata

# Autres valeurs du config, définies par les besoins de env.py
# my_important_option = config.get_main_option("my_important_option")


def run_migrations_offline() -> None:
    """Exécuter les migrations en mode 'offline'.

    Ce mode configure le contexte avec juste une URL
    et non un Engine, bien qu'un Engine soit acceptable
    ici aussi. En sautant la création de l'Engine, nous n'avons même pas besoin
    d'un DBAPI disponible.

    Les appels à context.execute() ici émettent la chaîne de caractères donnée
    au script de sortie.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécuter les migrations en mode 'online'.

    Dans ce scénario, nous devons créer un Engine
    et associer une connexion avec le contexte.
    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
