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
