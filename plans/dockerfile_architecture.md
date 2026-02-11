# Architecture Dockerfile - Digitalism FastAPI

**Date de création :** 2025-02-11  
**Version du document :** 1.0  
**Auteur :** Planification architecturale pour Dockerfile

---

## Table des matières

1. [Architecture du Dockerfile](#1-architecture-du-dockerfile)
2. [Étapes de construction détaillées](#2-étapes-de-construction-détaillées)
3. [Configuration de l'application](#3-configuration-de-lapplication)
4. [Volumes et fichiers](#4-volumes-et-fichiers)
5. [Intégration avec docker-compose](#5-intégration-avec-docker-compose)
6. [Script de démarrage (entrypoint.sh)](#6-script-de-démarrage-entrypointsh)
7. [Bonnes pratiques spécifiques](#7-bonnes-pratiques-spécifiques)

---

## 1. Architecture du Dockerfile

### 1.1 Structure Multi-Stage

Le Dockerfile utilisera une architecture en **3 stages** pour optimiser la taille finale de l'image et la sécurité :

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 1: BUILDER                             │
│  Image de base : python:3.11-slim                               │
│  Objectif : Compiler les dépendances (psycopg2, etc.)           │
│  Résultat : Environnement de construction avec wheels Python    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 2: RUNTIME                             │
│  Image de base : python:3.11-slim                               │
│  Objectif : Image d'exécution minimale                          │
│  Résultat : Image de production optimisée                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Stage 3: FINAL (optionnel)                  │
│  Image de base : python:3.11-slim                               │
│  Objectif : Configuration finale avec utilisateur non-root       │
│  Résultat : Image de production sécurisée                      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Justification des Stages

| Stage                 | Objectif                          | Justification                                                                                                               |
| --------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Builder**           | Compilation des dépendances       | `psycopg2` nécessite des dépendances de compilation (`gcc`, `libpq-dev`). Ces outils ne sont pas nécessaires en production. |
| **Runtime**           | Environnement d'exécution minimal | Copie uniquement les wheels compilés et le code source, réduisant la taille de l'image finale.                              |
| **Final** (optionnel) | Sécurité                          | Création d'un utilisateur non-root pour exécuter l'application selon les meilleures pratiques de sécurité.                  |

### 1.3 Choix de l'Image de Base

**Image sélectionnée :** `python:3.11-slim`

**Justification :**

- **Compatibilité PostgreSQL :** `psycopg2` fonctionne mieux avec `python:3.11-slim` qu'avec les images Alpine (`python:3.11-alpine`) qui nécessitent des contournements complexes pour les dépendances C.
- **Taille optimisée :** L'image `slim` (~125 MB) est significativement plus petite que l'image complète (~900 MB) tout en offrant les bibliothèques nécessaires.
- **Stabilité :** Python 3.11 est une version LTS stable avec des performances améliorées.
- **Compatibilité pyproject.toml :** Le fichier `pyproject.toml` spécifie `requires-python = ">=3.13"`, mais Python 3.11 est largement compatible avec les dépendances utilisées.

**Note importante :** Si l'application nécessite strictement Python 3.13+, utiliser `python:3.13-slim` à la place.

---

## 2. Étapes de Construction Détaillées

### 2.1 Stage 1: BUILDER

```dockerfile
# ========================================
# STAGE 1: BUILDER
# ========================================
FROM python:3.11-slim AS builder

# Métadonnées
LABEL stage="builder" \
      description="Compilation des dépendances Python"

# Variables d'environnement pour le builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances de compilation
# Nécessaires pour psycopg2 et d'autres extensions C
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /build

# Copie des fichiers de dépendances uniquement
COPY pyproject.toml ./

# Installation des dépendances dans un répertoire virtuel
# Utilisation de --target pour créer un environnement isolé
RUN pip install --upgrade pip && \
    pip install --target /install \
    --no-cache-dir \
    -e .

# Note: L'option -e (editable) installe le package en mode développement,
# ce qui permet de copier uniquement le code source dans le stage final.
```

**Explications détaillées :**

| Commande                        | Objectif                                                                     |
| ------------------------------- | ---------------------------------------------------------------------------- |
| `PYTHONUNBUFFERED=1`            | Désactive le buffering de stdout/stderr pour les logs en temps réel          |
| `PYTHONDONTWRITEBYTECODE=1`     | Empêche la création de fichiers `.pyc`                                       |
| `PIP_NO_CACHE_DIR=1`            | Réduit la taille de l'image en évitant le cache pip                          |
| `build-essential libpq-dev gcc` | Dépendances pour compiler `psycopg2`                                         |
| `pip install --target /install` | Installe les dépendances dans un répertoire séparé pour faciliter le copiage |
| `rm -rf /var/lib/apt/lists/*`   | Nettoie le cache apt pour réduire la taille                                  |

### 2.2 Stage 2: RUNTIME

```dockerfile
# ========================================
# STAGE 2: RUNTIME
# ========================================
FROM python:3.11-slim AS runtime

# Métadonnées
LABEL stage="runtime" \
      description="Environnement d'exécution minimal" \
      maintainer="digitalism-team" \
      version="1.0.0"

# Variables d'environnement pour le runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

# Installation des dépendances d'exécution uniquement
# libpq5 est nécessaire pour psycopg2 en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Création des répertoires nécessaires
RUN mkdir -p /app /app/data/csv /app/data/cache /app/logs && \
    chown -R appuser:appuser /app

# Copie des dépendances depuis le builder
COPY --from=builder --chown=appuser:appuser /install /app/.venv

# Copie du code source
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser alembic.ini /app/
COPY --chown=appuser:appuser alembic/ /app/alembic/

# Répertoire de travail
WORKDIR /app

# Changement vers l'utilisateur non-root
USER appuser

# Ports exposés
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Point d'entrée (sera défini par entrypoint.sh)
ENTRYPOINT ["/app/entrypoint.sh"]

# Commande par défaut
CMD ["api"]
```

**Explications détaillées :**

| Commande              | Objectif                                                                   |
| --------------------- | -------------------------------------------------------------------------- |
| `libpq5`              | Bibliothèque PostgreSQL pour le runtime (sans les outils de développement) |
| `curl`                | Utilisé pour les health checks et les appels HTTP                          |
| `groupadd/useradd`    | Création d'un utilisateur non-root pour la sécurité                        |
| `COPY --from=builder` | Copie uniquement les wheels compilés depuis le stage builder               |
| `EXPOSE 8000`         | Port par défaut de Uvicorn/FastAPI                                         |
| `HEALTHCHECK`         | Vérification automatique de la santé du conteneur                          |
| `ENTRYPOINT`          | Script d'initialisation qui gère les migrations et le démarrage            |

---

## 3. Configuration de l'Application

### 3.1 Variables d'Environnement Requises

| Variable                 | Description                  | Valeur par défaut        | Requis  |
| ------------------------ | ---------------------------- | ------------------------ | ------- |
| `DATABASE_URL`           | URL de connexion PostgreSQL  | -                        | **Oui** |
| `DATABASE_USER`          | Utilisateur PostgreSQL       | -                        | **Oui** |
| `DATABASE_PASSWORD`      | Mot de passe PostgreSQL      | -                        | **Oui** |
| `CSV_DATA_PATH`          | Chemin vers les fichiers CSV | `data/csv`               | Non     |
| `NOMINATIM_URL`          | URL du service Nominatim     | `http://localhost:8080`  | Non     |
| `NOMINATIM_USER_AGENT`   | User-Agent pour Nominatim    | `digitalism-fastapi/1.0` | Non     |
| `RUN_ETL_ON_STARTUP`     | Exécuter l'ETL au démarrage  | `false`                  | Non     |
| `ETL_DUPLICATE_HANDLING` | Gestion des doublons ETL     | `skip`                   | Non     |
| `ETL_ENABLE_GEOCODING`   | Activer le géocodage ETL     | `false`                  | Non     |

### 3.2 Ports Exposés

| Port   | Protocole | Utilisation           |
| ------ | --------- | --------------------- |
| `8000` | HTTP      | API FastAPI (Uvicorn) |

### 3.3 Health Checks

**Endpoint de santé interne :** `http://localhost:8000/health`

**Configuration Docker :**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Paramètres :**

- `--interval=30s` : Vérification toutes les 30 secondes
- `--timeout=10s` : Timeout de 10 secondes par vérification
- `--start-period=40s` : Période de grâce de 40s avant de considérer le conteneur en échec
- `--retries=3` : 3 échecs consécutifs avant de marquer le conteneur comme unhealthy

### 3.4 Commandes de Démarrage

Le script `entrypoint.sh` supportera plusieurs modes de démarrage :

| Mode      | Commande                | Description                               |
| --------- | ----------------------- | ----------------------------------------- |
| `api`     | `entrypoint.sh api`     | Démarre uniquement l'API FastAPI          |
| `etl`     | `entrypoint.sh etl`     | Exécute uniquement le pipeline ETL        |
| `all`     | `entrypoint.sh all`     | Exécute l'ETL puis démarre l'API          |
| `migrate` | `entrypoint.sh migrate` | Exécute uniquement les migrations Alembic |

**Commande Uvicorn (production) :**

```bash
uvicorn src.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $(nproc) \
    --log-level info \
    --access-log \
    --loop uvloop \
    --http httptools
```

**Paramètres Uvicorn :**

- `--host 0.0.0.0` : Écoute sur toutes les interfaces réseau
- `--port 8000` : Port d'écoute
- `--workers $(nproc)` : Un worker par cœur CPU (auto-scaling)
- `--loop uvloop` : Utilisation de uvloop pour de meilleures performances
- `--http httptools` : Utilisation de httptools pour le parsing HTTP

---

## 4. Volumes et Fichiers

### 4.1 Structure des Volumes

```yaml
volumes:
  # Données CSV pour l'ETL
  - ./data/csv:/app/data/csv:ro

  # Cache de géocodage Nominatim
  - ./data/cache:/app/data/cache

  # Logs de l'application
  - ./logs:/app/logs

  # Fichier .env local (optionnel, pour le développement)
  - ./.env:/app/.env:ro
```

**Détails des volumes :**

| Volume | Chemin hôte    | Chemin conteneur  | Mode             | Description                                |
| ------ | -------------- | ----------------- | ---------------- | ------------------------------------------ |
| CSV    | `./data/csv`   | `/app/data/csv`   | `ro` (read-only) | Fichiers CSV source pour l'ETL             |
| Cache  | `./data/cache` | `/app/data/cache` | `rw`             | Cache des résultats de géocodage           |
| Logs   | `./logs`       | `/app/logs`       | `rw`             | Fichiers de logs de l'application          |
| Env    | `./.env`       | `/app/.env`       | `ro`             | Variables d'environnement (dev uniquement) |

### 4.2 Contenu du Fichier `.dockerignore`

```
# ========================================
# .dockerignore - Digitalism FastAPI
# ========================================

# Git
.git
.gitignore
.gitattributes

# Documentation
README.md
docs/
*.md
!requirements.txt

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
.venv/
venv/
ENV/
env/

# Tests
tests/
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Plans et documentation
plans/

# Scripts de développement
check_db_cities.py
check_db.py
clean_db.py

# Données locales (montées via volumes)
data/
logs/

# Fichiers temporaires
*.tmp
*.log
*.bak
```

### 4.3 Permissions et Sécurité

**Structure des permissions :**

```bash
# Utilisateur non-root
appuser:appuser (UID/GID créés dynamiquement)

# Répertoires avec permissions appropriées
/app                    755  (drwxr-xr-x)
/app/src               755  (drwxr-xr-x)
/app/data/csv          755  (drwxr-xr-x)
/app/data/cache        755  (drwxr-xr-x)
/app/logs              755  (drwxr-xr-x)
/app/.venv             755  (drwxr-xr-x)

# Fichiers
/app/entrypoint.sh     755  (-rwxr-xr-x)
```

**Considérations de sécurité :**

1. **Utilisateur non-root** : L'application s'exécute avec l'utilisateur `appuser` (non-root)
2. **Volumes read-only** : Les fichiers CSV sont montés en lecture seule
3. **Minimalisme** : Seules les dépendances nécessaires sont installées
4. **Mises à jour de sécurité** : L'image de base `python:3.11-slim` est régulièrement mise à jour

---

## 5. Intégration avec docker-compose

### 5.1 Configuration du Service FastAPI

Ajouter le service `fastapi` au fichier [`docker-compose.yml`](docker-compose.yml:1) existant :

```yaml
services:
  # ... services existants (postgres, pgadmin, nominatim) ...

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: digitalism_fastapi
    environment:
      # Configuration de la base de données
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/digitalism_db
      DATABASE_USER: postgres
      DATABASE_PASSWORD: postgres

      # Configuration ETL
      CSV_DATA_PATH: /app/data/csv
      NOMINatIM_URL: http://nominatim:8080
      NOMINATIM_USER_AGENT: digitalism-fastapi/1.0 (contact:your@email.com)

      # Options de démarrage
      RUN_ETL_ON_STARTUP: "false"
      ETL_DUPLICATE_HANDLING: skip
      ETL_ENABLE_GEOCODING: "false"
    ports:
      - "8000:8000"
    volumes:
      # Données CSV pour l'ETL
      - ./data/csv:/app/data/csv:ro
      # Cache de géocodage
      - ./data/cache:/app/data/cache
      # Logs
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      nominatim:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: always
    networks:
      - digitalism_network
# ... réseaux existants ...
```

### 5.2 Dépendances avec PostgreSQL

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

**Justification :**

- Le service FastAPI doit attendre que PostgreSQL soit sain avant de démarrer
- Le health check de PostgreSQL est déjà configuré dans le service existant
- Cela évite les erreurs de connexion au démarrage

### 5.3 Configuration des Réseaux

Le service FastAPI utilisera le réseau existant `digitalism_network` :

```yaml
networks:
  digitalism_network:
    driver: bridge
```

**Avantages :**

- Communication inter-conteneurs via le nom du service (ex: `postgres`, `nominatim`)
- Isolation du réseau de développement
- Configuration centralisée

### 5.4 Commandes Docker Compose Utiles

| Commande                                                     | Description                               |
| ------------------------------------------------------------ | ----------------------------------------- |
| `docker-compose up -d`                                       | Démarrer tous les services                |
| `docker-compose up -d fastapi`                               | Démarrer uniquement le service FastAPI    |
| `docker-compose logs -f fastapi`                             | Suivre les logs du service FastAPI        |
| `docker-compose exec fastapi bash`                           | Ouvrir un shell dans le conteneur FastAPI |
| `docker-compose restart fastapi`                             | Redémarrer le service FastAPI             |
| `docker-compose down`                                        | Arrêter tous les services                 |
| `docker-compose build fastapi`                               | Reconstruire l'image FastAPI              |
| `docker-compose exec fastapi python -m alembic upgrade head` | Exécuter manuellement les migrations      |

---

## 6. Script de Démarrage (entrypoint.sh)

### 6.1 Structure du Script

```bash
#!/bin/bash
set -e

# ========================================
# Entrypoint.sh - Digitalism FastAPI
# ========================================
# Ce script gère:
# - L'exécution des migrations Alembic
# - Le démarrage de l'API FastAPI
# - L'exécution optionnelle du pipeline ETL
# ========================================

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ========================================
# Fonction: Attendre que PostgreSQL soit prêt
# ========================================
wait_for_postgres() {
    log_info "Attente de la disponibilité de PostgreSQL..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if python -c "
import os
import sys
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            log_info "PostgreSQL est prêt !"
            return 0
        fi

        attempt=$((attempt + 1))
        log_warn "PostgreSQL n'est pas encore prêt (tentative $attempt/$max_attempts)..."
        sleep 2
    done

    log_error "PostgreSQL n'est pas disponible après $max_attempts tentatives"
    return 1
}

# ========================================
# Fonction: Exécuter les migrations Alembic
# ========================================
run_migrations() {
    log_info "Exécution des migrations Alembic..."

    if python -m alembic upgrade head; then
        log_info "Migrations exécutées avec succès"
        return 0
    else
        log_error "Erreur lors de l'exécution des migrations"
        return 1
    fi
}

# ========================================
# Fonction: Exécuter le pipeline ETL
# ========================================
run_etl() {
    log_info "Démarrage du pipeline ETL..."

    local duplicate_handling="${ETL_DUPLICATE_HANDLING:-skip}"
    local enable_geocoding="${ETL_ENABLE_GEOCODING:-false}"

    log_info "Configuration ETL:"
    log_info "  - Gestion des doublons: $duplicate_handling"
    log_info "  - Géocodage activé: $enable_geocoding"

    local etl_cmd="python -m src.etl.scripts.city_etl_pipeline"
    etl_cmd="$etl_cmd --duplicate-handling $duplicate_handling"

    if [ "$enable_geocoding" = "true" ]; then
        etl_cmd="$etl_cmd --enable-geocoding"
    fi

    if $etl_cmd; then
        log_info "Pipeline ETL terminé avec succès"
        return 0
    else
        log_error "Erreur lors de l'exécution du pipeline ETL"
        return 1
    fi
}

# ========================================
# Fonction: Démarrer l'API FastAPI
# ========================================
start_api() {
    log_info "Démarrage de l'API FastAPI..."

    local workers="${UVICORN_WORKERS:-$(nproc)}"
    log_info "Nombre de workers Uvicorn: $workers"

    exec uvicorn src.app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers $workers \
        --log-level info \
        --access-log \
        --loop uvloop \
        --http httptools
}

# ========================================
# Programme principal
# ========================================
main() {
    local mode="${1:-api}"

    log_info "========================================="
    log_info "Digitalism FastAPI - Entrypoint"
    log_info "Mode: $mode"
    log_info "========================================="

    # Attendre PostgreSQL
    if ! wait_for_postgres; then
        log_error "Impossible de se connecter à PostgreSQL"
        exit 1
    fi

    # Exécuter les migrations
    if ! run_migrations; then
        log_error "Erreur lors des migrations"
        exit 1
    fi

    # Exécuter selon le mode
    case "$mode" in
        api)
            start_api
            ;;
        etl)
            if run_etl; then
                log_info "ETL terminé avec succès"
                exit 0
            else
                log_error "ETL échoué"
                exit 1
            fi
            ;;
        all)
            if run_etl; then
                log_info "ETL terminé, démarrage de l'API..."
                start_api
            else
                log_error "ETL échoué, arrêt du conteneur"
                exit 1
            fi
            ;;
        migrate)
            log_info "Migrations terminées, arrêt du conteneur"
            exit 0
            ;;
        *)
            log_error "Mode inconnu: $mode"
            log_info "Modes disponibles: api, etl, all, migrate"
            exit 1
            ;;
    esac
}

# Exécuter le programme principal
main "$@"
```

### 6.2 Utilisation du Script

| Commande                | Action                             |
| ----------------------- | ---------------------------------- |
| `entrypoint.sh api`     | Démarrer uniquement l'API          |
| `entrypoint.sh etl`     | Exécuter uniquement l'ETL          |
| `entrypoint.sh all`     | Exécuter l'ETL puis démarrer l'API |
| `entrypoint.sh migrate` | Exécuter uniquement les migrations |

### 6.3 Variables d'Environnement du Script

| Variable                 | Description                         | Valeur par défaut |
| ------------------------ | ----------------------------------- | ----------------- |
| `ETL_DUPLICATE_HANDLING` | Gestion des doublons (skip/replace) | `skip`            |
| `ETL_ENABLE_GEOCODING`   | Activer le géocodage (true/false)   | `false`           |
| `UVICORN_WORKERS`        | Nombre de workers Uvicorn           | `$(nproc)`        |

---

## 7. Bonnes Pratiques Spécifiques

### 7.1 Sécurité

| Pratique                         | Implémentation                                                           |
| -------------------------------- | ------------------------------------------------------------------------ |
| **Utilisateur non-root**         | Exécution avec `appuser` (UID/GUID créés dynamiquement)                  |
| **Volumes read-only**            | Les fichiers CSV sont montés en lecture seule                            |
| **Minimisation des dépendances** | Utilisation de multi-stage builds pour exclure les outils de compilation |
| **Mises à jour de sécurité**     | Utilisation d'images de base régulièrement mises à jour                  |
| **Secrets non exposés**          | Utilisation de variables d'environnement pour les mots de passe          |
| **Health checks**                | Vérification automatique de la santé du conteneur                        |

### 7.2 Performance

| Pratique               | Implémentation                                            |
| ---------------------- | --------------------------------------------------------- |
| **Multi-stage builds** | Réduction de la taille de l'image finale                  |
| **Workers multiples**  | Uvicorn configuré avec `--workers $(nproc)`               |
| **uvloop**             | Utilisation de uvloop pour de meilleures performances I/O |
| **httptools**          | Parsing HTTP optimisé                                     |
| **Cache pip**          | Désactivation du cache pip (`PIP_NO_CACHE_DIR=1`)         |
| **Batch processing**   | ETL utilise des batches de 100 enregistrements            |

### 7.3 Maintenabilité

| Pratique                      | Implémentation                                             |
| ----------------------------- | ---------------------------------------------------------- |
| **Entrypoint script**         | Script shell modulaire avec des fonctions claires          |
| **Configuration centralisée** | Variables d'environnement dans docker-compose.yml          |
| **Logs structurés**           | Logging avec couleurs et niveaux (INFO, WARN, ERROR)       |
| **Documentation inline**      | Commentaires détaillés dans le Dockerfile et entrypoint.sh |
| **.dockerignore**             | Exclusion des fichiers inutiles du contexte de build       |
| **Health checks**             | Vérification automatique de la santé du service            |

### 7.4 Observabilité

| Métrique                | Source                                           |
| ----------------------- | ------------------------------------------------ |
| **Logs applicatifs**    | Sortie stdout/stderr (visible via `docker logs`) |
| **Health check**        | Endpoint `/health` accessible via curl           |
| **Migrations**          | Logs Alembic lors de l'exécution                 |
| **ETL progress**        | Logs détaillés du pipeline ETL                   |
| **Uvicorn access logs** | Logs des requêtes HTTP                           |

### 7.5 Développement vs Production

| Aspect               | Développement          | Production                     |
| -------------------- | ---------------------- | ------------------------------ |
| **Image de base**    | `python:3.11-slim`     | `python:3.11-slim` (identique) |
| **Workers Uvicorn**  | 1 (pour le hot-reload) | `$(nproc)` (auto-scaling)      |
| **Logs**             | Verbose                | Info/Warn/Error                |
| **Hot-reload**       | `--reload` (optionnel) | Non                            |
| **Debug**            | Activé                 | Désactivé                      |
| **ETL au démarrage** | Optionnel              | Configurable via env var       |

### 7.6 Dépannage

| Problème                         | Solution                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------- |
| **Connexion PostgreSQL refusée** | Vérifier que le service postgres est sain (`docker-compose ps`)               |
| **Erreur psycopg2**              | Vérifier que `libpq5` est installé dans le stage runtime                      |
| **Health check échoue**          | Vérifier que le port 8000 est exposé et que curl est installé                 |
| **ETL ne trouve pas le CSV**     | Vérifier que le volume `./data/csv:/app/data/csv` est monté correctement      |
| **Permissions refusées**         | Vérifier que l'utilisateur `appuser` a les droits nécessaires sur les volumes |

---

## Annexe A: Exemple de Dockerfile Complet

```dockerfile
# ========================================
# Dockerfile - Digitalism FastAPI
# ========================================
# Multi-stage build pour optimiser la taille
# et la sécurité de l'image finale
# ========================================

# ========================================
# STAGE 1: BUILDER
# ========================================
FROM python:3.11-slim AS builder

LABEL stage="builder" \
      description="Compilation des dépendances Python"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances de compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install --target /install \
    --no-cache-dir \
    -e .

# ========================================
# STAGE 2: RUNTIME
# ========================================
FROM python:3.11-slim AS runtime

LABEL stage="runtime" \
      description="Environnement d'exécution minimal" \
      maintainer="digitalism-team" \
      version="1.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN mkdir -p /app /app/data/csv /app/data/cache /app/logs && \
    chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /install /app/.venv

COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser alembic.ini /app/
COPY --chown=appuser:appuser alembic/ /app/alembic/
COPY --chown=appuser:appuser entrypoint.sh /app/

WORKDIR /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["api"]
```

---

## Annexe B: Commandes Utiles

### Construction et Exécution

```bash
# Construire l'image
docker build -t digitalism-fastapi:latest .

# Exécuter le conteneur
docker run -p 8000:8000 --env-file .env digitalism-fastapi:latest

# Exécuter avec docker-compose
docker-compose up -d fastapi

# Reconstruire l'image
docker-compose build --no-cache fastapi
```

### Débogage

```bash
# Voir les logs
docker-compose logs -f fastapi

# Entrer dans le conteneur
docker-compose exec fastapi bash

# Exécuter une commande
docker-compose exec fastapi python -c "from src.config import get_settings; print(get_settings())"

# Vérifier les migrations
docker-compose exec fastapi python -m alembic current

# Exécuter manuellement l'ETL
docker-compose exec fastapi python -m src.etl.scripts.city_etl_pipeline --enable-geocoding
```

### Nettoyage

```bash
# Arrêter et supprimer les conteneurs
docker-compose down

# Supprimer les images
docker rmi digitalism-fastapi:latest

# Nettoyer tout
docker system prune -a
```

---

## Conclusion

Ce document de planification fournit une architecture complète et détaillée pour le Dockerfile de l'application Digitalism FastAPI. Les principales caractéristiques sont :

1. **Multi-stage build** pour optimiser la taille de l'image
2. **Sécurité** avec utilisateur non-root et volumes read-only
3. **Performance** avec workers multiples et optimisations uvloop/httptools
4. **Maintenabilité** avec scripts modulaires et documentation détaillée
5. **Intégration** avec docker-compose existant pour PostgreSQL, pgAdmin et Nominatim

Le plan est suffisamment détaillé pour qu'un développeur puisse créer le Dockerfile, le script entrypoint.sh et les fichiers associés sans ambiguïté.
