import os
import sys
import json
from pathlib import Path

# Setup paths
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import (
    Base,
    Organization,
    User,
    LeadSource,
    SourcePermission,
    IndiaLocation,
    Company,
    Branch,
    BusinessContact,
    SocialProfile,
)


def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "default-org").first()
        if not org:
            org = Organization(
                name="India Leads Default Organization",
                slug="default-org",
                is_active=True
            )
            db.add(org)
            db.flush()
            print(f"Created organization: {org.name} ({org.id})")
        else:
            print(f"Found organization: {org.name}")

        # 2. Admin User
        admin = db.query(User).filter(User.email == "admin@indialeads.internal").first()
        if not admin:
            admin = User(
                organization_id=org.id,
                email="admin@indialeads.internal",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="Principal Lead Admin",
                is_superuser=True,
                is_active=True
            )
            db.add(admin)
            db.flush()
            print(f"Created admin user: {admin.email}")
        else:
            admin.hashed_password = get_password_hash("Admin@123456")
            db.flush()
            print(f"Updated admin user password: {admin.email}")

        # 3. Lead Sources & Permissions
        sources_def = [
            {
                "code": "demo_fixture",
                "name": "Deterministic Demo Fixture",
                "description": "Built-in realistic sample businesses labeled DEMO DATA for offline testing.",
                "requires_api_key": False,
                "permission": {
                    "license_name": "Demo Test License",
                    "permitted_storage": True,
                    "permitted_export": True,
                    "permitted_enrichment": True,
                    "notes": "Clearly labeled DEMO DATA in UI and exports."
                }
            },
            {
                "code": "licensed_csv",
                "name": "Licensed Commercial Lead Import",
                "description": "User-imported CSV or XLSX records with verified commercial usage license.",
                "requires_api_key": False,
                "permission": {
                    "license_name": "Commercial B2B Directory License",
                    "permitted_storage": True,
                    "permitted_export": True,
                    "permitted_enrichment": True,
                    "notes": "Full permission to store, enrich, and export."
                }
            },
            {
                "code": "google_places",
                "name": "Google Places API (Discovery Preview)",
                "description": "Official Google Places discovery adapter. For discovery preview only; restricted from permanent export without independent licensing.",
                "requires_api_key": True,
                "permission": {
                    "license_name": "Google Maps Platform Terms",
                    "permitted_storage": False,
                    "permitted_export": False,
                    "permitted_enrichment": False,
                    "notes": "Compliant temporary preview only. Place IDs cached up to 30 days."
                }
            },
            {
                "code": "google_search",
                "name": "Google Custom Search API",
                "description": "Authorized Google Search API adapter for discovering public business URLs.",
                "requires_api_key": True,
                "permission": {
                    "license_name": "Google Custom Search JSON API Terms",
                    "permitted_storage": True,
                    "permitted_export": False,
                    "permitted_enrichment": True,
                    "notes": "Search API query URLs used for crawling website domains."
                }
            }
        ]

        source_map = {}
        for s_def in sources_def:
            src = db.query(LeadSource).filter(LeadSource.code == s_def["code"]).first()
            if not src:
                src = LeadSource(
                    code=s_def["code"],
                    name=s_def["name"],
                    description=s_def["description"],
                    is_active=True,
                    requires_api_key=s_def["requires_api_key"]
                )
                db.add(src)
                db.flush()

                perm = SourcePermission(
                    source_id=src.id,
                    license_name=s_def["permission"]["license_name"],
                    permitted_storage=s_def["permission"]["permitted_storage"],
                    permitted_export=s_def["permission"]["permitted_export"],
                    permitted_enrichment=s_def["permission"]["permitted_enrichment"],
                    notes=s_def["permission"]["notes"]
                )
                db.add(perm)
                db.flush()
                print(f"Created LeadSource: {src.code}")
            source_map[src.code] = src

        # 4. India Locations
        locations_file = ROOT_DIR / "data" / "locations" / "india_states_cities.json"
        if locations_file.exists():
            with open(locations_file, "r", encoding="utf-8") as f:
                loc_data = json.load(f)
            
            existing_loc_count = db.query(IndiaLocation).count()
            if existing_loc_count == 0:
                print(f"Seeding {len(loc_data)} India locations...")
                for item in loc_data:
                    loc = IndiaLocation(
                        state=item["state"],
                        district=item.get("district"),
                        city=item["city"],
                        locality=item.get("locality"),
                        pincode=item.get("pincode"),
                        is_active=True
                    )
                    db.add(loc)
                db.flush()
                print("Seeded India locations successfully.")

        # 5. Deterministic Demo Leads
        demo_leads_file = ROOT_DIR / "database" / "seed" / "demo_leads.json"
        if demo_leads_file.exists():
            with open(demo_leads_file, "r", encoding="utf-8") as f:
                demo_data = json.load(f)

            existing_branches = db.query(Branch).filter(Branch.is_demo == True).count()
            if existing_branches == 0:
                print(f"Seeding {len(demo_data)} demo leads...")
                demo_source = source_map.get("demo_fixture")
                for lead in demo_data:
                    # Find or create company
                    norm_company_name = lead["company_name"].lower().strip()
                    company = db.query(Company).filter(
                        Company.organization_id == org.id,
                        Company.normalized_name == norm_company_name
                    ).first()
                    if not company:
                        company = Company(
                            organization_id=org.id,
                            legal_name=lead["company_name"],
                            normalized_name=norm_company_name,
                            website_domain=lead.get("website_domain"),
                            primary_category=lead["category"],
                            description=lead.get("description")
                        )
                        db.add(company)
                        db.flush()

                    norm_branch_name = lead["branch_name"].lower().strip()
                    branch = Branch(
                        company_id=company.id,
                        branch_name=lead["branch_name"],
                        normalized_branch_name=norm_branch_name,
                        address_line=lead.get("address_line"),
                        locality=lead.get("locality"),
                        city=lead["city"],
                        district=lead.get("district"),
                        state=lead["state"],
                        pincode=lead.get("pincode"),
                        country="India",
                        website_url=lead.get("website_url"),
                        is_headquarters=lead.get("is_headquarters", False),
                        source_id=demo_source.id if demo_source else None,
                        source_reference="DEMO-FIXTURE-" + norm_branch_name.replace(" ", "-"),
                        source_permission_status="permitted_storage",
                        confidence_score=1.0,
                        enrichment_status="completed",
                        is_demo=True,
                        is_active=True
                    )
                    db.add(branch)
                    db.flush()

                    # Add contacts
                    for contact in lead.get("contacts", []):
                        val = contact["value"].strip()
                        # Clean phone for normalized value
                        norm_val = val
                        if contact["type"] in ["mobile", "landline", "whatsapp"]:
                            digits = "".join(ch for ch in val if ch.isdigit() or ch == '+')
                            if not digits.startswith("+91") and len(digits) == 10:
                                norm_val = f"+91{digits}"
                            else:
                                norm_val = digits
                        elif contact["type"] == "email":
                            norm_val = val.lower()

                        b_contact = BusinessContact(
                            branch_id=branch.id,
                            contact_type=contact["type"],
                            original_value=val,
                            normalized_value=norm_val,
                            is_primary=True,
                            is_verified=True,
                            source="demo_fixture"
                        )
                        db.add(b_contact)

                    # Add social profiles
                    for soc in lead.get("socials", []):
                        sp = SocialProfile(
                            branch_id=branch.id,
                            platform=soc["platform"],
                            profile_url=soc["url"],
                            handle=soc.get("handle")
                        )
                        db.add(sp)

                db.flush()
                print("Seeded demo leads successfully.")

        db.commit()
        print("Seed completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

