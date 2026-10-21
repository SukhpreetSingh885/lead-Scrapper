import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, engine
from app.models import Branch, Company, LeadSource, SourcePermission, IndiaLocation
import sqlalchemy as sa


def run_migration():
    print("=" * 60)
    print("MIGRATION: Quarantine Demo Leads & Setup Overpass Source")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Add is_archived and archive_reason to branches if not present
        with engine.connect() as conn:
            # Check branches columns
            inspector = sa.inspect(engine)
            columns = [c["name"] for c in inspector.get_columns("branches")]
            
            if "is_archived" not in columns:
                print("Adding is_archived column to branches table...")
                conn.execute(sa.text("ALTER TABLE branches ADD COLUMN is_archived BOOLEAN DEFAULT 0 NOT NULL"))
                conn.commit()
            else:
                print("Column is_archived already exists on branches.")

            if "archive_reason" not in columns:
                print("Adding archive_reason column to branches table...")
                conn.execute(sa.text("ALTER TABLE branches ADD COLUMN archive_reason VARCHAR(255)"))
                conn.commit()
            else:
                print("Column archive_reason already exists on branches.")

        # 2. Quarantine demo branches
        demo_branches = db.query(Branch).filter(
            sa.or_(
                Branch.is_demo == True,
                Branch.source_reference.like("DEMO-%")
            )
        ).all()

        print(f"Found {len(demo_branches)} demo branch records to quarantine.")
        for b in demo_branches:
            b.is_archived = True
            b.is_demo = True
            b.is_active = False
            b.archive_reason = "Quarantined legacy demo fixture"
        db.commit()
        print("Successfully quarantined all demo records.")

        # 3. Add or update Overpass lead source
        overpass_src = db.query(LeadSource).filter(LeadSource.code == "overpass").first()
        if not overpass_src:
            print("Creating 'overpass' LeadSource record...")
            overpass_src = LeadSource(
                id=str(uuid.uuid4()),
                name="OpenStreetMap Overpass API",
                code="overpass",
                description="Live business discovery powered by OpenStreetMap Overpass API under ODbL license.",
                is_active=True,
                requires_api_key=False
            )
            db.add(overpass_src)
            db.flush()

            # Add source permissions
            perm = SourcePermission(
                id=str(uuid.uuid4()),
                source_id=overpass_src.id,
                license_name="Open Data Commons Open Database License (ODbL) 1.0",
                permitted_storage=True,
                permitted_export=True,
                permitted_enrichment=True,
                license_terms_url="https://www.openstreetmap.org/copyright",
                notes="Permitted for CRM storage, website enrichment, and lead generation export with source attribution."
            )
            db.add(perm)
            db.commit()
            print("Created 'overpass' LeadSource and permissions.")
        else:
            print("'overpass' LeadSource already exists.")

        # 4. Enrich india_locations with geographic coordinates
        city_coords = {
            "Mohali": (30.7046, 76.7179),
            "Chandigarh": (30.7333, 76.7794),
            "Ludhiana": (30.9010, 75.8573),
            "Amritsar": (31.6340, 74.8723),
            "Jalandhar": (31.3260, 75.5762),
            "Delhi": (28.6139, 77.2090),
            "Mumbai": (19.0760, 72.8777),
            "Pune": (18.5204, 73.8567),
            "Bengaluru": (12.9716, 77.5946),
            "Jaipur": (26.9124, 75.7873),
            "Chennai": (13.0827, 80.2707),
            "Hyderabad": (17.3850, 78.4867),
            "Ahmedabad": (23.0225, 72.5714),
            "Kolkata": (22.5726, 88.3639),
            "Gurugram": (28.4595, 77.0266),
            "Noida": (28.5355, 77.3910)
        }

        locations = db.query(IndiaLocation).all()
        updated_locs = 0
        for loc in locations:
            if loc.city in city_coords:
                lat, lon = city_coords[loc.city]
                loc.latitude = lat
                loc.longitude = lon
                updated_locs += 1
        db.commit()
        print(f"Updated {updated_locs} location records with geographic coordinates.")

        print("Migration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()

