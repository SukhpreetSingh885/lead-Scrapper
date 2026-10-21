import pytest
import io
import openpyxl
from sqlalchemy import text
from app.models import Branch, Company, DiscoveryJob, DiscoveryJobItem, BusinessContact, LeadSource, SourcePermission
from app.models.job import discovery_job_leads
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.exports.csv_export import CsvExportService
from app.services.exports.excel_export import ExcelExportService
from app.schemas.lead import LeadFilterParams
from app.repositories.lead_repo import LeadRepository
from app.workers.tasks.export_tasks import execute_export_generation
from app.models.export import Export
import json
import uuid


@pytest.mark.asyncio
async def test_category_filtering_and_job_isolation(db_session):
    """
    Comprehensive verification of all 9 requirements:
    Test 1: Search Mohali + Gym -> All returned businesses match Gym.
    Test 2: Search Mohali + Cafe -> No unrelated gym/salon in Cafe results.
    Test 3: Search Mohali + Salon -> Only matching salons appear.
    Test 4: Search Gym again -> Deduplication prevents duplicate branches.
    Test 5: LeadRepository with Gym filter -> Only gyms appear.
    Test 6: LeadRepository without filters -> All saved categories appear.
    Test 7: Contact-qualified export for Gym -> Only gyms with valid contact number exported.
    Test 8: Job-specific result counts and pagination.
    Test 9: Association of previously existing business with new search job.
    """
    provider = OverpassDiscoveryProvider()
    db = db_session
    org_id = "test-org-1"

    # ----------------------------------------------------
    # TEST 1: Search Mohali + Gym
    # ----------------------------------------------------
    gym_leads = await provider.search(location="Mohali", category="Gym", max_results=20)
    assert len(gym_leads) >= 2, f"Expected at least 2 gyms, found {len(gym_leads)}"
    for lead in gym_leads:
        assert lead.category == "Gym", f"Lead '{lead.business_name}' had category '{lead.category}', expected 'Gym'"
        # Check source tags do not have cafe or salon tags
        raw_tags = lead.raw_payload.get("tags", {})
        assert raw_tags.get("amenity") not in ("cafe", "restaurant"), f"Unrelated amenity in gym lead: {lead.business_name}"
        assert raw_tags.get("shop") not in ("hairdresser", "beauty"), f"Unrelated shop in gym lead: {lead.business_name}"

    # ----------------------------------------------------
    # TEST 2: Search Mohali + Cafe
    # ----------------------------------------------------
    cafe_leads = await provider.search(location="Mohali", category="Cafe", max_results=20)
    assert len(cafe_leads) >= 2, f"Expected at least 2 cafes, found {len(cafe_leads)}"
    for lead in cafe_leads:
        assert lead.category == "Cafe", f"Lead '{lead.business_name}' had category '{lead.category}', expected 'Cafe'"
        raw_tags = lead.raw_payload.get("tags", {})
        assert raw_tags.get("leisure") not in ("fitness_centre", "sports_centre"), f"Gym tag found in cafe lead: {lead.business_name}"
        assert raw_tags.get("shop") not in ("hairdresser", "beauty"), f"Salon tag found in cafe lead: {lead.business_name}"

    # ----------------------------------------------------
    # TEST 3: Search Mohali + Salon
    # ----------------------------------------------------
    salon_leads = await provider.search(location="Mohali", category="Salon", max_results=20)
    assert len(salon_leads) >= 2, f"Expected at least 2 salons, found {len(salon_leads)}"
    for lead in salon_leads:
        assert lead.category == "Salon", f"Lead '{lead.business_name}' had category '{lead.category}', expected 'Salon'"
        raw_tags = lead.raw_payload.get("tags", {})
        assert raw_tags.get("amenity") not in ("cafe", "restaurant"), f"Cafe tag in salon lead: {lead.business_name}"
        assert raw_tags.get("leisure") not in ("fitness_centre", "sports_centre"), f"Gym tag in salon lead: {lead.business_name}"

    # ----------------------------------------------------
    # Setup Search Jobs & Save Leads into Database
    # ----------------------------------------------------
    resolver = DeduplicationResolver(db)

    # Job A: Gym Search Job
    job_gym = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Gym",
        max_leads=20,
        source_code="overpass",
        status="completed"
    )
    db.add(job_gym)
    db.flush()

    gym_saved_branches = []
    seen_gym_branch_ids = set()
    for item in gym_leads:
        branch, action = resolver.process_discovered_lead(item, org_id)
        if branch and branch.id not in seen_gym_branch_ids:
            seen_gym_branch_ids.add(branch.id)
            gym_saved_branches.append(branch)
            db.execute(
                discovery_job_leads.insert().values(job_id=job_gym.id, branch_id=branch.id)
            )
    db.commit()

    # Job B: Cafe Search Job
    job_cafe = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Cafe",
        max_leads=20,
        source_code="overpass",
        status="completed"
    )
    db.add(job_cafe)
    db.flush()

    cafe_saved_branches = []
    seen_cafe_branch_ids = set()
    for item in cafe_leads:
        branch, action = resolver.process_discovered_lead(item, org_id)
        if branch and branch.id not in seen_cafe_branch_ids:
            seen_cafe_branch_ids.add(branch.id)
            cafe_saved_branches.append(branch)
            db.execute(
                discovery_job_leads.insert().values(job_id=job_cafe.id, branch_id=branch.id)
            )
    db.commit()

    # ----------------------------------------------------
    # TEST 4: Run Gym search again -> No Duplicate Branches created
    # ----------------------------------------------------
    initial_branch_count = db.query(Branch).count()
    second_pass_branches = []
    for item in gym_leads:
        branch, action = resolver.process_discovered_lead(item, org_id)
        assert action == "updated", f"Expected 'updated' on duplicate lead, got '{action}'"
        second_pass_branches.append(branch)
    final_branch_count = db.query(Branch).count()
    assert final_branch_count == initial_branch_count, "Running search again created duplicate branches!"

    # ----------------------------------------------------
    # TEST 5: Open All Leads with Gym filter -> Only Gyms appear
    # ----------------------------------------------------
    lead_repo = LeadRepository(db)
    gym_results, gym_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams(category="Gym")
    )
    assert gym_total > 0
    for lead in gym_results:
        assert lead.category == "Gym", f"Unrelated category {lead.category} found when filtering for Gym"

    # ----------------------------------------------------
    # TEST 6: Reset filters -> All saved categories appear
    # ----------------------------------------------------
    all_results, all_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams()
    )
    all_categories = {lead.category for lead in all_results}
    assert "Gym" in all_categories
    assert "Cafe" in all_categories
    assert all_total >= (len(gym_saved_branches) + len(cafe_saved_branches))

    # ----------------------------------------------------
    # TEST 7: Contact-Qualified Export for Gym Leads
    # ----------------------------------------------------
    # Find or create at least one gym with phone and one without phone
    gym_with_phone = None
    gym_without_phone = None
    for b in gym_saved_branches:
        has_num = any(c.contact_type in ("mobile", "landline", "phone", "whatsapp") for c in b.contacts)
        if has_num and not gym_with_phone:
            gym_with_phone = b
        elif not has_num and not gym_without_phone:
            gym_without_phone = b

    if not gym_with_phone and gym_saved_branches:
        # Add a test phone to first gym
        gym_with_phone = gym_saved_branches[0]
        db.add(BusinessContact(
            branch_id=gym_with_phone.id,
            contact_type="mobile",
            original_value="+919876543210",
            normalized_value="+919876543210",
            is_primary=True,
            is_verified=True,
            source="test"
        ))
        db.commit()

    qualified_gyms, qualified_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams(category="Gym", has_contact_number=True)
    )
    assert qualified_total >= 1
    for qg in qualified_gyms:
        assert qg.category == "Gym"
        assert qg.primary_mobile or qg.primary_landline or qg.primary_whatsapp

    # Test CSV Export with contact qualification
    csv_bytes = CsvExportService.generate_csv_bytes([db.query(Branch).filter(Branch.id == qg.id).first() for qg in qualified_gyms])
    csv_text = csv_bytes.decode("utf-8-sig")
    assert "Gym" in csv_text
    assert "Cafe" not in csv_text
    assert "Salon" not in csv_text

    # Test Excel Export with contact qualification
    xlsx_bytes = ExcelExportService.generate_xlsx_bytes([db.query(Branch).filter(Branch.id == qg.id).first() for qg in qualified_gyms])
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    ws = wb.active
    assert ws.max_row == len(qualified_gyms) + 1  # 1 header + qualified rows

    # ----------------------------------------------------
    # TEST 8: Job-specific result counts and pagination
    # ----------------------------------------------------
    job_gym_leads, job_gym_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams(job_id=job_gym.id, page=1, page_size=2)
    )
    assert job_gym_total == len(gym_saved_branches)
    assert len(job_gym_leads) <= 2
    for item in job_gym_leads:
        assert item.category == "Gym"

    # Verify Cafe job results are completely isolated
    job_cafe_leads, job_cafe_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams(job_id=job_cafe.id)
    )
    assert job_cafe_total == len(cafe_saved_branches)
    for item in job_cafe_leads:
        assert item.category == "Cafe"

    # ----------------------------------------------------
    # TEST 9: Existing business associated with a new matching search job
    # ----------------------------------------------------
    new_gym_job = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Gym",
        max_leads=20,
        source_code="overpass",
        status="completed"
    )
    db.add(new_gym_job)
    db.flush()

    # Associate existing gym branch to this new job
    existing_gym_branch = gym_saved_branches[0]
    db.execute(
        discovery_job_leads.insert().values(job_id=new_gym_job.id, branch_id=existing_gym_branch.id)
    )
    db.commit()

    new_job_leads, new_job_total = lead_repo.get_leads_paginated(
        org_id=org_id,
        filters=LeadFilterParams(job_id=new_gym_job.id)
    )
    assert new_job_total == 1
    assert new_job_leads[0].id == existing_gym_branch.id
    assert new_job_leads[0].business_name == existing_gym_branch.branch_name
