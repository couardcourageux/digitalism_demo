#!/usr/bin/env python3
"""
Script de nettoyage de la base de données.
Supprime toutes les régions et départements.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from src.database import SessionLocal
from src.model.region import Region
from src.model.department import Department

def main():
    print("=" * 70)
    print("NETTOYAGE DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Compter avant nettoyage
        regions_count = db.query(Region).count()
        departments_count = db.query(Department).count()
        
        print(f"\nÉtat avant nettoyage:")
        print(f"  - Régions: {regions_count}")
        print(f"  - Départements: {departments_count}")
        
        # Supprimer les départements (d'abord car ils dépendent des régions)
        departments_deleted = db.query(Department).delete()
        print(f"\n✓ {departments_deleted} département(s) supprimé(s)")
        
        # Supprimer les régions
        regions_deleted = db.query(Region).delete()
        print(f"✓ {regions_deleted} région(s) supprimée(s)")
        
        # Committer les changements
        db.commit()
        print("\n✓ Changements commités avec succès")
        
        # Vérifier après nettoyage
        regions_count_after = db.query(Region).count()
        departments_count_after = db.query(Department).count()
        
        print(f"\nÉtat après nettoyage:")
        print(f"  - Régions: {regions_count_after}")
        print(f"  - Départements: {departments_count_after}")
        
        if regions_count_after == 0 and departments_count_after == 0:
            print("\n✓ Base de données nettoyée avec succès!")
        else:
            print("\n⚠️  Attention: Il reste encore des données dans la base")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
