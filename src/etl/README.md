# ETL (Extract, Transform, Load) - Digitalism FastAPI

Ce module contient les composants ETL pour l'ingestion de données dans l'application Digitalism FastAPI.

## Architecture

L'architecture ETL est basée sur des composants modulaires et réutilisables:

### Composants de base

- **BaseComponent**: Classe abstraite fournissant la structure de base pour tous les composants ETL
- **BaseExtractor**: Interface pour l'extraction de données depuis différentes sources
- **BaseTransformer**: Interface pour la transformation des données extraites
- **BaseLoader**: Interface pour le chargement des données transformées dans la base de données

### Extracteurs

- **CSVReader**: Lecteur de fichiers CSV avec support pour le décodage UTF-8 et la gestion des erreurs

### Transformeurs

- **RegionTransformer**: Transformation des données des régions
- **DepartmentTransformer**: Transformation des données des départements
- **CityTransformer**: Transformation des données des communes

### Loaders

- **CityLoader**: Chargement des données des communes dans la base de données avec gestion des doublons

### Scripts

- **generate_regions_departments_json.py**: Script pour générer le JSON des régions et départements
- **city_etl_pipeline.py**: Pipeline ETL principal pour l'ingestion des communes

## Utilisation

### Pipeline ETL pour les communes

Le script principal `city_etl_pipeline.py` permet d'ingérer les données des communes depuis un fichier CSV:

```bash
python -m src.etl.scripts.city_etl_pipeline
```

Le pipeline effectue les étapes suivantes:

1. Configuration et initialisation du logger
2. Extraction des données depuis le fichier CSV
3. Transformation des données (normalisation, validation)
4. Chargement des données dans la base de données avec gestion des doublons

### Configuration

La configuration ETL est définie dans `src/etl/config.py`:

- Chemins des fichiers d'entrée
- Stratégies de gestion des doublons
- Paramètres de traitement par lot (batch size)

## Géocodage des communes

Le pipeline ETL intègre un service de géocodage utilisant l'API Nominatim (OpenStreetMap) pour enrichir les données des communes avec leurs coordonnées GPS.

### Architecture du service de géocodage

Le service de géocodage est implémenté dans [`src/etl/services/geocoding.py`](src/etl/services/geocoding.py) et repose sur les composants suivants:

#### Classes principales

- **`GeocodingService`**: Service principal de géocodage
  - Gère les requêtes vers l'API Nominatim
  - Implémente un cache persistant pour éviter les requêtes redondantes
  - Applique un rate limiting pour respecter les politiques d'utilisation de l'API
  - Gère les erreurs avec mécanisme de retry

- **`GeocodingResult`**: Dataclass représentant le résultat d'une requête de géocodage
  - `latitude`: Latitude de la ville
  - `longitude`: Longitude de la ville
  - `source`: Source des données ('cache' ou 'api')
  - `display_name`: Nom complet de la ville (ex: "Paris, Île-de-France, France")
  - `city`: Nom de la ville
  - `postcode`: Code postal

#### Intégration dans le pipeline ETL

Le géocodage est intégré dans [`CityTransformer`](src/etl/transformers/city_transformer.py) :

1. Le transformer extrait les coordonnées GPS depuis le CSV si disponibles
2. Si les coordonnées sont manquantes et que le géocodage est activé, le service est appelé
3. Le résultat du géocodage est utilisé pour compléter les données de la commune

### Configuration

#### Variables d'environnement

Le service de géocodage est configurable via les variables d'environnement suivantes dans le fichier [`.env`](.env):

```bash
# URL de base de l'API Nominatim
# Par défaut: http://localhost:8080
# Pour utiliser l'instance publique: https://nominatim.openstreetmap.org
NOMINATIM_URL=http://localhost:8080

# User-Agent pour les requêtes HTTP (requis par Nominatim)
# Remplacez contact:your@email.com par votre adresse email
NOMINATIM_USER_AGENT=digitalism-fastapi/1.0 (contact:your@email.com)
```

#### Paramètres de configuration

Les paramètres suivants sont définis dans [`src/etl/config.py`](src/etl/config.py):

| Paramètre               | Valeur par défaut                 | Description                                    |
| ----------------------- | --------------------------------- | ---------------------------------------------- |
| `NOMINATIM_BASE_URL`    | `settings.NOMINATIM_URL`          | URL de base de l'API Nominatim                 |
| `NOMINATIM_USER_AGENT`  | `settings.NOMINATIM_USER_AGENT`   | User-Agent pour les requêtes HTTP              |
| `NOMINATIM_RATE_LIMIT`  | `1.0`                             | Délai minimum entre les requêtes (en secondes) |
| `NOMINATIM_CACHE_FILE`  | `data/cache/geocoding_cache.json` | Chemin du fichier de cache                     |
| `NOMINATIM_MAX_RETRIES` | `3`                               | Nombre maximum de tentatives en cas d'erreur   |
| `NOMINATIM_RETRY_DELAY` | `2.0`                             | Délai entre les tentatives (en secondes)       |

### Utilisation

#### Activation du géocodage

Le géocodage est désactivé par défaut. Pour l'activer, utilisez l'option `--enable-geocoding` :

```bash
# Import sans géocodage (par défaut)
python -m src.etl.scripts.city_etl_pipeline

# Import avec géocodage des villes sans coordonnées
python -m src.etl.scripts.city_etl_pipeline --enable-geocoding

# Import avec géocodage et gestion des doublons
python -m src.etl.scripts.city_etl_pipeline --enable-geocoding --duplicate-handling replace
```

#### Comportement du géocodage

- Le géocodage est effectué uniquement pour les communes sans coordonnées GPS dans le CSV
- Les communes déjà géocodées dans le cache ne déclenchent pas de requête API
- Le service respecte le rate limiting configuré (1 requête/seconde par défaut)
- En cas d'échec du géocodage, la commune est quand même importée mais sans coordonnées

#### Utilisation directe du service

Le service de géocodage peut également être utilisé directement dans votre code:

```python
from src.etl.services.geocoding import GeocodingService

# Initialiser le service
geocoding_service = GeocodingService()

# Géocoder une ville
result = geocoding_service.geocode("Paris", "75001")

if result:
    print(f"Latitude: {result.latitude}")
    print(f"Longitude: {result.longitude}")
    print(f"Source: {result.source}")  # 'cache' ou 'api'
    print(f"Nom complet: {result.display_name}")
```

### Cache de géocodage

#### Fonctionnement

Le cache de géocodage est un fichier JSON persistant (`data/cache/geocoding_cache.json`) qui stocke les résultats des requêtes de géocodage:

- **Clé de cache**: `{nom_ville}_{code_postal}` (en minuscules)
- **Données stockées**: latitude, longitude, display_name, city, postcode
- **Avantages**:
  - Réduction du nombre de requêtes API
  - Accélération des imports ultérieurs
  - Respect des politiques d'utilisation de Nominatim

#### Structure du fichier de cache

```json
{
  "paris_75001": {
    "latitude": 48.865633,
    "longitude": 2.321236,
    "display_name": "Paris, 1er Arrondissement, Paris, Île-de-France, France métropolitaine, 75001, France",
    "city": "Paris",
    "postcode": "75001"
  },
  "lyon_69001": {
    "latitude": 45.769527,
    "longitude": 4.836023,
    "display_name": "Lyon, 1er Arrondissement, Lyon, Rhône, Auvergne-Rhône-Alpes, France métropolitaine, 69001, France",
    "city": "Lyon",
    "postcode": "69001"
  }
}
```

#### Gestion du cache

- Le cache est automatiquement chargé au démarrage du service
- Le cache est sauvegardé après chaque nouvelle entrée
- Si le fichier de cache est corrompu, il est ignoré et un nouveau cache vide est créé
- Pour réinitialiser le cache, supprimez simplement le fichier `data/cache/geocoding_cache.json`

#### Exemple de logs

```
INFO - Cache de géocodage chargé: 1523 entrées
DEBUG - Cache hit pour PARIS (75001)
INFO - Géocodage de LYON (69001) via API Nominatim
INFO - Géocodage réussi pour LYON (69001): 45.769527, 4.836023 (source: api)
DEBUG - Cache de géocodage sauvegardé: 1524 entrées
```

## Données

### Modèles de données

Les modèles de données ETL sont définis dans `src/etl/utils/data_models.py`:

- `RegionData`: Données brutes des régions
- `DepartmentData`: Données brutes des départements
- `CityData`: Données brutes des communes

### Helpers

- `csv_helpers.py`: Fonctions utilitaires pour la manipulation de fichiers CSV
- `logger.py`: Configuration du logging pour les composants ETL

## Tests

Les tests ETL doivent être placés dans `tests/test_etl/` et suivre les conventions de test du projet.

## Développement

Pour ajouter un nouveau type de données:

1. Définir le modèle de données dans `data_models.py`
2. Créer un transformeur héritant de `BaseTransformer`
3. Créer un loader héritant de `BaseLoader`
4. Créer un script de pipeline orchestrant les composants
