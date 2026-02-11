# Digitalism FastAPI

API FastAPI pour la gestion des régions, départements et villes françaises.

## Stack technologique

- **FastAPI** : Framework web moderne et performant
- **SQLAlchemy 2.0** : ORM avec typage amélioré
- **PostgreSQL 16** : Base de données relationnelle
- **Pydantic v2** : Validation des données et configuration
- **Docker Compose** : Infrastructure de développement

## Installation

### Prérequis

- Python 3.13 ou supérieur
- Docker et Docker Compose
- uv (gestionnaire de paquets Python) ou pip

### Installation des dépendances

```bash
# Avec uv (recommandé)
uv sync

# Ou avec pip
pip install -e .
```

### Configuration

Créez un fichier `.env` à la racine du projet (utilisez `.env.example` comme modèle) :

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/digitalism_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
CSV_DATA_PATH=data/csv
```

## Démarrage

### Démarrage de la base de données

```bash
docker-compose up -d
```

Cela démarre PostgreSQL et PgAdmin. Les données sont persistées dans le dossier `data/docker/`.

### Démarrage du serveur de développement

```bash
# Avec uv
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# Ou avec pip
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

### Vérification

Ouvrez votre navigateur sur :

- API : <http://localhost:8000>
- Documentation interactive : <http://localhost:8000/docs>
- PgAdmin : <http://localhost:5050> (email: <admin@digitalism.com>, password: admin)

## Structure du projet

```
digitalism_fastapi/
├── src/                    # Code source de l'application
│   ├── app.py             # Instance FastAPI
│   ├── config.py          # Configuration Pydantic Settings
│   ├── database.py        # Gestion des sessions DB
│   ├── model/            # Modèles SQLAlchemy
│   ├── schemas/          # Schémas Pydantic
│   ├── repository/       # Pattern Repository
│   ├── routes/           # Routes API
│   └── utils/           # Utilitaires
├── alembic/              # Migrations de base de données
├── data/                 # Données (non versionné)
├── reviews/              # Reviews de codebase
├── docker-compose.yml     # Orchestration Docker
├── pyproject.toml       # Configuration du projet
└── README.md            # Ce fichier
```

## Architecture

L'application suit une architecture en couches avec le pattern Repository :

```
Routes FastAPI → Schemas Pydantic → Repositories → Modèles SQLAlchemy → PostgreSQL
```

## Points forts

- Stack moderne et cohérente (FastAPI, SQLAlchemy 2.0, Pydantic v2)
- Architecture en couches bien structurée
- Gestion robuste des données (Soft Delete, Timestamps UTC, Validation Pydantic)
- Configuration centralisée via Pydantic Settings
- Infrastructure Docker Compose pour le développement

## Documentation API

La documentation interactive est disponible sur <http://localhost:8000/docs> une fois le serveur démarré.

## Licence

MIT

## Auteur

couardcourageux
