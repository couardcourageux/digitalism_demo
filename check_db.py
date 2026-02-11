#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'état de la base de données.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from src.database import SessionLocal, engine
from sqlalchemy import inspect, text
from src.model.region import Region
from src.model.department import Department

def main():
    print("=" * 70)
    print("DIAGNOSTIC DE LA BASE DE DONNÉES")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Vérifier les tables existantes
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables existantes: {tables}")
        
        # Compter les régions
        regions_count = db.query(Region).count()
        print(f"\nNombre de régions en base: {regions_count}")
        
        # Vérifier les doublons de régions
        duplicate_regions = db.execute(
            text("""
                SELECT name, COUNT(*) as count
                FROM regions
                GROUP BY name
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        if duplicate_regions:
            print(f"\n⚠️  {len(duplicate_regions)} région(s) en double détectée(s):")
            for name, count in duplicate_regions:
                print(f"   - {name}: {count} occurrences")
        else:
            print("\n✓ Aucun doublon de région détecté")
        
        # Lister toutes les régions
        print("\nListe des régions en base:")
        regions = db.query(Region).order_by(Region.name).all()
        for region in regions:
            print(f"   - ID: {region.id}, Nom: {region.name}")
        
        # Compter les départements
        departments_count = db.query(Department).count()
        print(f"\nNombre de départements en base: {departments_count}")
        
        # Vérifier les doublons de départements
        duplicate_departments = db.execute(
            text("""
                SELECT name, code_departement, COUNT(*) as count
                FROM departments
                GROUP BY name, code_departement
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        if duplicate_departments:
            print(f"\n⚠️  {len(duplicate_departments)} département(s) en double détecté(s):")
            for name, code, count in duplicate_departments:
                print(f"   - {name} ({code}): {count} occurrences")
        else:
            print("\n✓ Aucun doublon de département détecté")
        
        # Lister les départements
        print("\nListe des départements en base (premiers 20):")
        departments = db.query(Department).order_by(Department.name).limit(20).all()
        for dept in departments:
            print(f"   - ID: {dept.id}, Nom: {dept.name}, Code: {dept.code_departement}, Région ID: {dept.region_id}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
