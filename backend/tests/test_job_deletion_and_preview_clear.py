import pytest
import uuid
from app.models import (
    Branch,
    Company,
    DiscoveryJob,
    DiscoveryJobItem,
    BusinessContact,
    Organization,
    User,
)
from app.models.job import discovery_job_leads


@pytest.mark.asyncio
async def test_clear_job_preview_preserves_job_and_saved_leads(client, db_session):
    """
    Test Requirement 2 & 5:
    - Clear Preview removes unsaved preview results without deleting the search job.
    - Preserves already saved preview items.
    - Does not delete any businesses in the permanent CRM.
    """
    db = db_session
    org_id = "test-org-1"

    # 1. Create a discovery job
    job = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Chandigarh",
        resolved_city="Chandigarh",
        resolved_state="Chandigarh",
        category="Gym",
        max_leads=10,
        source_code="overpass",
        status="completed",
        total_discovered=3,
        total_eligible=3,
        total_inserted=1,
        total_updated=0,
    )
    db.add(job)
    db.flush()

    # 2. Create 1 permanent CRM branch
    company = Company(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        legal_name="Chandigarh Iron Gym",
        normalized_name="chandigarh iron gym",
        primary_category="Gym",
    )
    db.add(company)
    db.flush()

    saved_branch = Branch(
        id=str(uuid.uuid4()),
        company_id=company.id,
        branch_name="Chandigarh Iron Gym Sector 17",
        normalized_branch_name="chandigarh iron gym sector 17",
        city="Chandigarh",
        state="Chandigarh",
        is_active=True,
    )
    db.add(saved_branch)
    db.flush()

    # 3. Add 3 preview items: 1 already saved, 2 unsaved
    item_saved = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job.id,
        business_name="Chandigarh Iron Gym Sector 17",
        city="Chandigarh",
        state="Chandigarh",
        category="Gym",
        is_eligible_for_crm=True,
        is_saved=True,
        branch_id=saved_branch.id,
    )
    item_unsaved_1 = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job.id,
        business_name="Temporary Fitness Center",
        city="Chandigarh",
        state="Chandigarh",
        category="Gym",
        is_eligible_for_crm=True,
        is_saved=False,
    )
    item_unsaved_2 = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job.id,
        business_name="Unwanted Yoga Studio",
        city="Chandigarh",
        state="Chandigarh",
        category="Gym",
        is_eligible_for_crm=True,
        is_saved=False,
    )
    unsaved_id_1 = item_unsaved_1.id
    unsaved_id_2 = item_unsaved_2.id
    saved_id = item_saved.id
    saved_branch_id = saved_branch.id

    db.add_all([item_saved, item_unsaved_1, item_unsaved_2])
    db.commit()

    # 4. Invoke Clear Preview endpoint
    res = client.delete(f"/api/v1/discovery/jobs/{job.id}/preview")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["cleared_count"] == 2
    assert data["remaining_items"] == 1

    # 5. Verify database state
    db.refresh(job)
    assert job.id is not None, "Search job must still exist"
    assert job.total_discovered == 1
    assert job.total_eligible == 1

    # Unsaved items are deleted
    assert db.query(DiscoveryJobItem).filter(DiscoveryJobItem.id == unsaved_id_1).first() is None
    assert db.query(DiscoveryJobItem).filter(DiscoveryJobItem.id == unsaved_id_2).first() is None

    # Saved item is preserved
    assert db.query(DiscoveryJobItem).filter(DiscoveryJobItem.id == saved_id).first() is not None

    # CRM branch is completely preserved
    crm_branch = db.query(Branch).filter(Branch.id == saved_branch_id).first()
    assert crm_branch is not None
    assert crm_branch.branch_name == "Chandigarh Iron Gym Sector 17"


@pytest.mark.asyncio
async def test_delete_search_job_removes_previews_and_preserves_crm_leads(client, db_session):
    """
    Test Requirements 1, 4, 5, 6, 8, 9, 10:
    - Deleting a search job removes the job and its temporary preview items.
    - Permanent CRM businesses (Branch, Company) are NOT deleted.
    - Association in discovery_job_leads is cleaned up safely without foreign-key errors.
    - Other search jobs and admin users are unaffected.
    """
    db = db_session
    org_id = "test-org-1"

    # 1. Create permanent CRM Company and Branch
    company = Company(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        legal_name="Mohali Dental Care",
        normalized_name="mohali dental care",
        primary_category="Clinic",
    )
    db.add(company)
    db.flush()

    branch = Branch(
        id=str(uuid.uuid4()),
        company_id=company.id,
        branch_name="Mohali Dental Clinic Phase 7",
        normalized_branch_name="mohali dental clinic phase 7",
        city="Mohali",
        state="Punjab",
        is_active=True,
    )
    db.add(branch)
    db.flush()

    # 2. Create Job A (target job to delete)
    job_a = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Clinic",
        max_leads=20,
        source_code="overpass",
        status="completed",
        total_discovered=5,
        total_eligible=5,
        total_inserted=1,
    )
    db.add(job_a)
    db.flush()

    # Link Job A to branch in discovery_job_leads association table
    db.execute(
        discovery_job_leads.insert().values(job_id=job_a.id, branch_id=branch.id)
    )

    # Add temporary preview items to Job A
    item_a1 = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job_a.id,
        business_name="Unsaved Clinic Alpha",
        city="Mohali",
        state="Punjab",
        category="Clinic",
        is_eligible_for_crm=True,
        is_saved=False,
    )
    item_a2 = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job_a.id,
        business_name="Mohali Dental Clinic Phase 7",
        city="Mohali",
        state="Punjab",
        category="Clinic",
        is_eligible_for_crm=True,
        is_saved=True,
        branch_id=branch.id,
    )
    db.add_all([item_a1, item_a2])

    # 3. Create Job B (other search job - must NOT be deleted)
    job_b = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Salon",
        max_leads=10,
        source_code="overpass",
        status="completed",
        total_discovered=2,
    )
    db.add(job_b)
    db.commit()

    # Initial count of jobs
    initial_jobs_res = client.get("/api/v1/discovery/jobs").json()
    initial_job_count = initial_jobs_res["total"]

    # 4. Delete Job A via API
    del_res = client.delete(f"/api/v1/discovery/jobs/{job_a.id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["success"] is True
    assert del_data["deleted_job_id"] == job_a.id

    # 5. Verify Job A is gone
    assert db.query(DiscoveryJob).filter(DiscoveryJob.id == job_a.id).first() is None

    # 6. Verify preview items of Job A are gone
    assert db.query(DiscoveryJobItem).filter(DiscoveryJobItem.job_id == job_a.id).count() == 0

    # 7. Verify association table entries for Job A are gone
    assoc_check = db.execute(
        discovery_job_leads.select().where(discovery_job_leads.c.job_id == job_a.id)
    ).all()
    assert len(assoc_check) == 0

    # 8. CRITICAL REQUIREMENT 5: The permanent CRM branch and company MUST still exist!
    saved_crm_branch = db.query(Branch).filter(Branch.id == branch.id).first()
    assert saved_crm_branch is not None, "Branch in permanent CRM must NOT be deleted!"
    assert saved_crm_branch.branch_name == "Mohali Dental Clinic Phase 7"

    saved_crm_company = db.query(Company).filter(Company.id == company.id).first()
    assert saved_crm_company is not None, "Company in permanent CRM must NOT be deleted!"

    # 9. REQUIREMENT 6: Other search jobs and users are intact
    job_b_check = db.query(DiscoveryJob).filter(DiscoveryJob.id == job_b.id).first()
    assert job_b_check is not None, "Other search jobs must NOT be deleted!"

    user_check = db.query(User).filter(User.organization_id == org_id).first()
    assert user_check is not None, "Users must NOT be deleted!"

    # 10. REQUIREMENT 7: Jobs count immediately updated
    after_jobs_res = client.get("/api/v1/discovery/jobs").json()
    assert after_jobs_res["total"] == initial_job_count - 1


@pytest.mark.asyncio
async def test_delete_running_job_safely_cancels_and_deletes(client, db_session):
    """
    Test Requirement 9:
    - Running jobs are safely cancelled before deletion without crashing.
    """
    db = db_session
    org_id = "test-org-1"

    job_running = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        location_input="Chandigarh",
        resolved_city="Chandigarh",
        resolved_state="Chandigarh",
        category="Pharmacy",
        max_leads=50,
        source_code="overpass",
        status="running",
    )
    db.add(job_running)
    db.commit()

    del_res = client.delete(f"/api/v1/discovery/jobs/{job_running.id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    assert db.query(DiscoveryJob).filter(DiscoveryJob.id == job_running.id).first() is None


@pytest.mark.asyncio
async def test_delete_job_ownership_and_not_found(client, db_session):
    """
    Test Requirement 10:
    - Ownership checks: cannot delete a job belonging to another organization or nonexistent job.
    """
    db = db_session

    # Nonexistent job ID
    res_404 = client.delete(f"/api/v1/discovery/jobs/{uuid.uuid4()}")
    assert res_404.status_code == 404

    # Job belonging to another organization
    other_org = Organization(id="other-org-99", name="Other Org", slug="other-org")
    db.add(other_org)
    db.flush()

    other_job = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id=other_org.id,
        location_input="Delhi",
        resolved_city="Delhi",
        resolved_state="Delhi",
        category="Hotels",
        max_leads=10,
        source_code="overpass",
        status="completed",
    )
    db.add(other_job)
    db.commit()

    # User from test-org-1 tries to delete other-org-99's job
    res_forbidden = client.delete(f"/api/v1/discovery/jobs/{other_job.id}")
    assert res_forbidden.status_code == 404, "Should not be able to find or delete another org's job"
    assert db.query(DiscoveryJob).filter(DiscoveryJob.id == other_job.id).first() is not None
