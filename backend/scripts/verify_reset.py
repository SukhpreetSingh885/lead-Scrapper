import sys
import asyncio
import httpx
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from app.core.database import SessionLocal
from app.core.config import settings
from app.models import (
    User,
    Organization,
    IndiaLocation,
    Company,
    Branch,
    BusinessContact,
    DiscoveryJob,
    DiscoveryJobItem,
    EnrichmentJob,
    DuplicateCandidate,
    Export,
    LeadSource
)
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.services.deduplication.resolver import DeduplicationResolver


async def run_verification():
    print("=" * 60)
    print("RUNNING POST-RESET VERIFICATION SUITE")
    print("=" * 60)

    # 1. Direct Database Inspection
    print("\n[Step 1] Verifying Database Counts in Primary DB...")
    db = SessionLocal()
    try:
        users_cnt = db.query(User).count()
        orgs_cnt = db.query(Organization).count()
        locs_cnt = db.query(IndiaLocation).count()
        companies_cnt = db.query(Company).count()
        branches_cnt = db.query(Branch).count()
        contacts_cnt = db.query(BusinessContact).count()
        disc_jobs_cnt = db.query(DiscoveryJob).count()
        disc_items_cnt = db.query(DiscoveryJobItem).count()
        enrich_cnt = db.query(EnrichmentJob).count()
        dups_cnt = db.query(DuplicateCandidate).count()
        exports_cnt = db.query(Export).count()
        sources_cnt = db.query(LeadSource).count()

        print(f"  Companies: {companies_cnt} (Expected: 0)")
        print(f"  Branches: {branches_cnt} (Expected: 0)")
        print(f"  Business contacts: {contacts_cnt} (Expected: 0)")
        print(f"  Discovery jobs: {disc_jobs_cnt} (Expected: 0)")
        print(f"  Discovery job items: {disc_items_cnt} (Expected: 0)")
        print(f"  Enrichment jobs: {enrich_cnt} (Expected: 0)")
        print(f"  Duplicate candidates: {dups_cnt} (Expected: 0)")
        print(f"  Exports: {exports_cnt} (Expected: 0)")
        print(f"  Lead sources: {sources_cnt} (Expected: 0)")
        print(f"  Admin users: {users_cnt} (Preserved, Expected: 1)")
        print(f"  Organizations: {orgs_cnt} (Preserved, Expected: 1)")
        print(f"  India locations: {locs_cnt} (Preserved, Expected: 30)")

        assert companies_cnt == 0, f"Expected 0 companies, found {companies_cnt}"
        assert branches_cnt == 0, f"Expected 0 branches, found {branches_cnt}"
        assert contacts_cnt == 0, f"Expected 0 contacts, found {contacts_cnt}"
        assert disc_jobs_cnt == 0, f"Expected 0 discovery jobs, found {disc_jobs_cnt}"
        assert disc_items_cnt == 0, f"Expected 0 discovery items, found {disc_items_cnt}"
        assert enrich_cnt == 0, f"Expected 0 enrichment jobs, found {enrich_cnt}"
        assert dups_cnt == 0, f"Expected 0 duplicate candidates, found {dups_cnt}"
        assert exports_cnt == 0, f"Expected 0 exports, found {exports_cnt}"
        assert users_cnt >= 1, "Admin user missing!"
        assert locs_cnt >= 30, "India locations missing!"
        print("  --> Direct Database Count Checks: PASSED!")
    finally:
        db.close()

    # 2. HTTP API Login & Dashboard Verification
    base_url = "http://127.0.0.1:8001/api/v1"
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("\n[Step 2] Verifying Admin Authentication via API...")
        login_res = await client.post(
            f"{base_url}/auth/login",
            data={
                "username": settings.ADMIN_EMAIL or "admin@indialeads.internal",
                "password": settings.ADMIN_INITIAL_PASSWORD or "Admin@123456"
            }
        )
        print(f"  Login status: {login_res.status_code}")
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token_data = login_res.json()
        token = token_data.get("access_token")
        assert token, "Access token missing from login response"
        headers = {"Authorization": f"Bearer {token}"}
        print("  --> Admin Login Check: PASSED!")

        print("\n[Step 3] Verifying Dashboard Metrics via API...")
        metrics_res = await client.get(f"{base_url}/leads/metrics/dashboard", headers=headers)
        assert metrics_res.status_code == 200, f"Dashboard metrics failed: {metrics_res.text}"
        metrics = metrics_res.json()
        print(f"  Dashboard metrics payload: {metrics}")
        assert metrics.get("total_unique_leads") == 0, f"Expected 0 leads, got {metrics.get('total_unique_leads')}"
        assert metrics.get("active_jobs") == 0, f"Expected 0 active jobs, got {metrics.get('active_jobs')}"
        assert metrics.get("completed_jobs") == 0, f"Expected 0 completed jobs, got {metrics.get('completed_jobs')}"
        print("  --> Dashboard Zero-State Check: PASSED!")

        print("\n[Step 4] Verifying Leads List via API...")
        leads_res = await client.get(f"{base_url}/leads", headers=headers)
        assert leads_res.status_code == 200, f"Leads query failed: {leads_res.text}"
        leads_data = leads_res.json()
        print(f"  Total leads: {leads_data.get('total')}, items length: {len(leads_data.get('items', []))}")
        assert leads_data.get("total") == 0
        assert len(leads_data.get("items", [])) == 0
        print("  --> Leads Zero-State Check: PASSED!")

        print("\n[Step 5] Verifying Discovery Jobs List via API...")
        jobs_res = await client.get(f"{base_url}/discovery/jobs", headers=headers)
        assert jobs_res.status_code == 200, f"Jobs query failed: {jobs_res.text}"
        jobs_data = jobs_res.json()
        print(f"  Total jobs: {jobs_data.get('total')}, items length: {len(jobs_data.get('items', []))}")
        assert jobs_data.get("total") == 0
        assert len(jobs_data.get("items", [])) == 0
        print("  --> Jobs Zero-State Check: PASSED!")

    # 3. Verify Live Overpass Search Pipeline can create new records
    print("\n[Step 6] Testing Live Overpass Pipeline creation capability (transaction test with rollback)...")
    db = SessionLocal()
    try:
        provider = OverpassDiscoveryProvider()
        test_leads = await provider.search(location="Mohali", category="Gym", max_results=1)
        assert len(test_leads) >= 1, "Failed to fetch live Overpass element for Mohali + Gym"
        lead_sample = test_leads[0]
        print(f"  Fetched live business: {lead_sample.business_name} ({lead_sample.category})")

        org = db.query(Organization).first()
        resolver = DeduplicationResolver(db)
        branch_obj, insert_status = resolver.process_discovered_lead(lead_sample, org.id)
        assert branch_obj is not None, "Failed to create branch record!"
        assert insert_status in ("inserted", "updated"), f"Unexpected insert status: {insert_status}"
        
        # Verify branch and company exist in db
        branch = db.query(Branch).filter(Branch.id == branch_obj.id).first()
        assert branch is not None, "Branch not found in db!"
        assert branch.branch_name == lead_sample.business_name
        assert branch.source is not None
        assert branch.source.code == "overpass"
        print(f"  Created test branch: '{branch.branch_name}' attributed to source '{branch.source.name}'")

        # Clean up this single verification record immediately to maintain 100% zero-state
        db.close()
        from reset_leads_data import clean_database, DB_PATH
        clean_database(DB_PATH)
        print("  Cleaned up verification test lead cleanly.")
    except Exception as e:
        db.close()
        from reset_leads_data import clean_database, DB_PATH
        clean_database(DB_PATH)
        raise e

    # Re-verify database remains at 0
    db = SessionLocal()
    try:
        assert db.query(Company).count() == 0
        assert db.query(Branch).count() == 0
        assert db.query(DiscoveryJob).count() == 0
        print("  --> Live Overpass Capability Check & Zero-State Integrity: PASSED!")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("ALL POST-RESET VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_verification())
