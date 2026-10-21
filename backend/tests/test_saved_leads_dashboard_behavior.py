import pytest
import uuid
from app.models import (
    Branch,
    Company,
    DiscoveryJob,
    DiscoveryJobItem,
    BusinessContact,
    LeadSource,
    SourcePermission,
)
from app.models.job import discovery_job_leads


@pytest.mark.asyncio
async def test_global_metrics_vs_filtered_leads_isolation(client, db_session):
    """
    Test 1 & 2:
    - Global dashboard metrics returns global CRM saved leads.
    - Unsaved discovery preview records are excluded from CRM metrics and Saved Leads tables.
    - Active search job filter for an unsaved discovery job returns 0 saved leads.
    """
    db = db_session
    org_id = "test-org-1"

    # 1. Create 3 saved Gym branches in Mohali
    comp_gym = Company(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        legal_name="Mohali Fitness Corp",
        normalized_name="mohali fitness corp",
        primary_category="Gym",
    )
    db.add(comp_gym)
    db.flush()

    for i in range(3):
        branch = Branch(
            id=str(uuid.uuid4()),
            company_id=comp_gym.id,
            branch_name=f"Mohali Fitness Club {i+1}",
            normalized_branch_name=f"mohali fitness club {i+1}",
            city="Mohali",
            state="Punjab",
            is_active=True,
        )
        db.add(branch)
        db.flush()
        # Add mobile to 2 of them
        if i < 2:
            contact = BusinessContact(
                id=str(uuid.uuid4()),
                branch_id=branch.id,
                contact_type="mobile",
                original_value=f"+91987654321{i}",
                normalized_value=f"+91987654321{i}",
                is_verified=True,
            )
            db.add(contact)

    # 2. Create 2 saved Salon branches in Chandigarh
    comp_salon = Company(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        legal_name="Chandigarh Styling Salon",
        normalized_name="chandigarh styling salon",
        primary_category="Salon",
    )
    db.add(comp_salon)
    db.flush()

    for i in range(2):
        branch = Branch(
            id=str(uuid.uuid4()),
            company_id=comp_salon.id,
            branch_name=f"Style Studio {i+1}",
            normalized_branch_name=f"style studio {i+1}",
            city="Chandigarh",
            state="Chandigarh",
            is_active=True,
        )
        db.add(branch)
        db.flush()

    db.commit()

    # Verify Global Metrics: Total saved leads = 5 (3 Gyms + 2 Salons)
    metrics_res = client.get("/api/v1/leads/metrics/dashboard")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert metrics_data["total_saved_leads"] == 5
    assert metrics_data["leads_with_mobile"] == 2
    assert metrics_data["leads_missing_contacts"] == 3
    assert metrics_data["export_eligible_leads"] == 2

    # 3. Simulate a new Discovery Job: Fashion in Mohali
    # Discovers 10 businesses, kept in preview (is_saved=False)
    job_fashion = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Fashion",
        max_leads=50,
        source_code="overpass",
        status="completed",
        total_discovered=10,
        total_eligible=10,
        total_inserted=0,
        total_updated=0,
    )
    db.add(job_fashion)
    db.flush()

    preview_items = []
    for i in range(10):
        item = DiscoveryJobItem(
            id=str(uuid.uuid4()),
            job_id=job_fashion.id,
            business_name=f"Distinct Fashion Brand {i+1}",
            city="Mohali",
            state="Punjab",
            category="Fashion",
            phone=f"+9198111222{i:02d}" if i < 3 else None,
            is_eligible_for_crm=True,
            is_saved=False,
            is_already_saved=False,
        )
        db.add(item)
        preview_items.append(item)
    db.commit()

    # 4. Verify that unsaved discovery preview records are EXCLUDED from CRM statistics
    metrics_after_job = client.get("/api/v1/leads/metrics/dashboard").json()
    assert metrics_after_job["total_saved_leads"] == 5, "Unsaved preview records must not alter global saved leads"

    # 5. Verify that filtering by active search job returns 0 saved leads (because preview hasn't been saved yet)
    job_leads_res = client.get(f"/api/v1/leads?job_id={job_fashion.id}")
    assert job_leads_res.status_code == 200
    job_leads_data = job_leads_res.json()
    assert job_leads_data["total"] == 0
    assert len(job_leads_data["items"]) == 0

    # 6. Verify Reset Filters: Requesting /api/v1/leads without filters returns ALL 5 saved leads
    all_leads_res = client.get("/api/v1/leads")
    assert all_leads_res.status_code == 200
    all_leads_data = all_leads_res.json()
    assert all_leads_data["total"] == 5
    assert len(all_leads_data["items"]) == 5

    # 7. Verify category filter: Gym returns 3, Salon returns 2, Fashion returns 0
    gym_res = client.get("/api/v1/leads?category=Gym").json()
    assert gym_res["total"] == 3

    salon_res = client.get("/api/v1/leads?category=Salon").json()
    assert salon_res["total"] == 2

    fashion_res = client.get("/api/v1/leads?category=Fashion").json()
    assert fashion_res["total"] == 0, "No Fashion leads should be saved yet"


@pytest.mark.asyncio
async def test_manual_save_selected_updates_dashboard_and_table(client, db_session):
    """
    Test 3 & 4:
    - Manual Save Selected / Save All works from discovery preview.
    - Saving leads creates CRM records, updates discovery_job_leads, and flags is_saved=True.
    - Newly saved leads appear in the filtered table for that job_id.
    - Global dashboard metrics increment accordingly.
    """
    db = db_session
    org_id = "test-org-1"

    # Start with a clean discovery job
    job = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Boutique",
        max_leads=10,
        source_code="overpass",
        status="completed",
        total_discovered=3,
        total_eligible=3,
        total_inserted=0,
        total_updated=0,
    )
    db.add(job)
    db.flush()

    business_names = [
        "Vogue Couture House",
        "Royal Heritage Silks",
        "Urban Trendz Apparels"
    ]

    items = []
    for i, name in enumerate(business_names):
        item = DiscoveryJobItem(
            id=str(uuid.uuid4()),
            job_id=job.id,
            business_name=name,
            address=f"SCO {i+10}, Sector 70",
            city="Mohali",
            state="Punjab",
            category="Boutique",
            phone=f"+9198777000{i:02d}",
            is_eligible_for_crm=True,
            is_saved=False,
            is_already_saved=False,
        )
        db.add(item)
        items.append(item)
    db.commit()

    # Initial dashboard count
    initial_metrics = client.get("/api/v1/leads/metrics/dashboard").json()
    initial_total = initial_metrics["total_saved_leads"]

    # Before saving: 0 leads for this job
    assert client.get(f"/api/v1/leads?job_id={job.id}").json()["total"] == 0

    # Save 2 selected items
    selected_ids = [items[0].id, items[1].id]
    save_payload = {
        "job_id": job.id,
        "item_ids": selected_ids,
        "save_all_eligible": False,
    }
    save_res = client.post("/api/v1/leads/save-selected", json=save_payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["saved_count"] == 2
    assert save_data["already_existing_count"] == 0

    # Verify discovery job counter updated
    db.refresh(job)
    assert job.total_inserted == 2
    assert job.total_updated == 0

    # Verify preview items updated
    db.refresh(items[0])
    db.refresh(items[1])
    db.refresh(items[2])
    assert items[0].is_saved is True
    assert items[0].is_already_saved is False
    assert items[1].is_saved is True
    assert items[1].is_already_saved is False
    assert items[2].is_saved is False

    # Filtered table by job_id now returns exactly 2 leads
    job_table_res = client.get(f"/api/v1/leads?job_id={job.id}").json()
    assert job_table_res["total"] == 2
    names = {l["business_name"] for l in job_table_res["items"]}
    assert "Vogue Couture House" in names
    assert "Royal Heritage Silks" in names

    # Global metrics incremented by 2
    updated_metrics = client.get("/api/v1/leads/metrics/dashboard").json()
    assert updated_metrics["total_saved_leads"] == initial_total + 2

    # Save the remaining eligible item using save_all_eligible=True
    save_all_payload = {
        "job_id": job.id,
        "save_all_eligible": True,
    }
    save_all_res = client.post("/api/v1/leads/save-selected", json=save_all_payload)
    assert save_all_res.status_code == 200
    save_all_data = save_all_res.json()
    assert save_all_data["saved_count"] == 1
    assert save_all_data["already_existing_count"] == 2

    # Table for job_id now returns all 3 leads
    assert client.get(f"/api/v1/leads?job_id={job.id}").json()["total"] == 3

    # Re-running save_all_eligible on already saved items reports 0 newly saved, 3 already existing
    dup_res = client.post("/api/v1/leads/save-selected", json=save_all_payload)
    assert dup_res.status_code == 200
    dup_data = dup_res.json()
    assert dup_data["saved_count"] == 0
    assert dup_data["already_existing_count"] == 3
