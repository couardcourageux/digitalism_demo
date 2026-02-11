# Dossier Data

Ce dossier contient les données utilisées par le projet, notamment les fichiers CSV sources et les fichiers JSON générés pour les migrations.

## Structure

```
data/
├── csv/
│   └── communes_departements.csv    # Fichier CSV source (à fournir)
└── regions_departments.json         # JSON généré pour migration Alembic
```

## Fichiers

### `csv/communes_departements.csv`

Fichier CSV source contenant les données des communes, départements et régions. Ce fichier doit être placé dans ce dossier pour que les scripts ETL puissent fonctionner.

**Colonnes attendues:**

- `nom_region`: Nom de la région
- `nom_departement`: Nom du département
- `code_departement`: Code INSEE du département

### `regions_departments.json`

Fichier JSON structuré généré par le script ETL. Ce fichier contient les régions et leurs départements associés, formaté pour être utilisé par une migration Alembic.

**Format:**

```json
{
  "regions": [
    {
      "nom": "NOM_RÉGION",
      "departements": [{ "code": "XX", "nom": "NOM_DÉPARTEMENT" }]
    }
  ]
}
```

## Régénérer le JSON

Pour régénérer le fichier `regions_departments.json` à partir du CSV source, exécutez:

```bash
python -m src.etl.scripts.generate_regions_departments_json
```

Cette commande:

1. Lit le fichier CSV `data/csv/communes_departements.csv`
2. Normalise et valide les données
3. Génère le JSON structuré dans `data/regions_departments.json`

## Utilisation dans les migrations

Le fichier `regions_departments.json` est utilisé par les migrations Alembic pour peupler la base de données avec les régions et départements.

**Note:** Ce fichier est une trace de méthode et ne doit pas être utilisé directement en production. Les données sont chargées en base de données via les migrations Alembic.

## Nettoyage

Pour nettoyer les fichiers générés:

```bash
rm data/regions_departments.json
```

**Attention:** Ne supprimez pas le fichier CSV source sans avoir une sauvegarde.
