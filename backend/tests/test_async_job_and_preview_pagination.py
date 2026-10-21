import json
import sqlite3
import pytest
from unittest.mock import patch
from app.models import DiscoveryJob, DiscoveryJobItem


def test_create_discovery_job_dispatches_background_task_promptly(auth_client, db_session):
    """
    Verifies that create_discovery_job returns DiscoveryJobOut immediately (non-blocking)
    via BackgroundTasks without hanging the HTTP request, even when Celery is not active.
    """
    with patch("app.api.v1.endpoints.discovery.execute_discovery_job") as mock_exec:
        mock_exec.return_value = None

        payload = {
            "location": "Chandigarh",
            "category": "Hospital",
            "max_leads": 100,
            "source": "overpass",
        }

        response = auth_client.post("/api/v1/discovery/jobs", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["category"] == "Hospital"
        assert data["resolved_city"] == "Chandigarh"
        assert data["status"] in ("pending", "queued", "running")

        # Verify job was persisted in database
        job = db_session.query(DiscoveryJob).filter(DiscoveryJob.id == data["id"]).first()
        assert job is not None
        assert job.category == "Hospital"

        # Repeated request with same category and city should return the existing active job
        repeat_response = auth_client.post("/api/v1/discovery/jobs", json=payload)
        assert repeat_response.status_code == 201
        assert repeat_response.json()["id"] == data["id"]


def test_preview_pagination_and_total_counts(auth_client, db_session):
    """
    Verifies that the /preview endpoint supports page sizes up to 500,
    calculates total_pages accurately, and returns paginated subsets.
    """
    # Create a test job
    job = DiscoveryJob(
        organization_id="test-org-1",
        location_input="Chandigarh",
        resolved_city="Chandigarh",
        resolved_state="Chandigarh",
        category="Hospital",
        max_leads=500,
        source_code="overpass",
        status="completed",
        total_discovered=75,
        total_eligible=75,
    )
    db_session.add(job)
    db_session.flush()

    # Add 75 dummy preview items
    for i in range(75):
        item = DiscoveryJobItem(
            job_id=job.id,
            business_name=f"Hospital {i+1}",
            category="Hospital",
            address=f"Sector {i % 30 + 1}, Chandigarh",
            city="Chandigarh",
            state="Chandigarh",
            phone=f"+91 172 260{i:04d}" if i % 2 == 0 else None,
            mobile=f"+91 98140{i:05d}" if i % 3 == 0 else None,
            whatsapp=f"+91 98140{i:05d}" if i % 5 == 0 else None,
            is_eligible_for_crm=True,
            is_saved=False,
            is_already_saved=(i % 10 == 0),
        )
        db_session.add(item)
    db_session.commit()

    # 1. Page 1 with pageSize 25 -> 25 items, total 75, total_pages 3
    res1 = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?page=1&page_size=25")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 75
    assert data1["page"] == 1
    assert data1["page_size"] == 25
    assert data1["total_pages"] == 3
    assert len(data1["items"]) == 25

    # 2. Page 3 with pageSize 25 -> 25 items
    res2 = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?page=3&page_size=25")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 25
    assert data2["page"] == 3

    # 3. Single page with pageSize 100 -> all 75 items returned at once
    res3 = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?page=1&page_size=100")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["total"] == 75
    assert data3["total_pages"] == 1
    assert len(data3["items"]) == 75


def test_preview_filters_mobile_landline_whatsapp(auth_client, db_session):
    """
    Verifies that preview endpoint filters correctly by:
    - must_have_mobile
    - must_have_landline
    - must_have_whatsapp
    - exclude_already_saved
    """
    job = DiscoveryJob(
        organization_id="test-org-1",
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Clinic",
        max_leads=100,
        source_code="overpass",
        status="completed",
    )
    db_session.add(job)
    db_session.flush()

    # Item 1: Mobile only
    item1 = DiscoveryJobItem(
        job_id=job.id,
        business_name="Mobile Only Clinic",
        mobile="+91 9876543210",
        phone=None,
        whatsapp=None,
        is_eligible_for_crm=True,
        is_already_saved=False,
    )
    # Item 2: Landline only
    item2 = DiscoveryJobItem(
        job_id=job.id,
        business_name="Landline Only Clinic",
        mobile=None,
        phone="+91 172 2223344",
        whatsapp=None,
        is_eligible_for_crm=True,
        is_already_saved=False,
    )
    # Item 3: Mobile + WhatsApp
    item3 = DiscoveryJobItem(
        job_id=job.id,
        business_name="WhatsApp Clinic",
        mobile="+91 9888812345",
        phone=None,
        whatsapp="+91 9888812345",
        is_eligible_for_crm=True,
        is_already_saved=True,
    )
    # Item 4: No phone
    item4 = DiscoveryJobItem(
        job_id=job.id,
        business_name="No Contact Clinic",
        mobile=None,
        phone=None,
        whatsapp=None,
        is_eligible_for_crm=True,
        is_already_saved=False,
    )

    db_session.add_all([item1, item2, item3, item4])
    db_session.commit()

    # Filter mobile: should match item1 and item3 (count = 2)
    res_mob = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?must_have_mobile=true")
    assert res_mob.status_code == 200
    assert res_mob.json()["total"] == 2
    names_mob = [it["business_name"] for it in res_mob.json()["items"]]
    assert "Mobile Only Clinic" in names_mob
    assert "WhatsApp Clinic" in names_mob
    assert "Landline Only Clinic" not in names_mob

    # Filter landline: should match only item2 (count = 1)
    res_land = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?must_have_landline=true")
    assert res_land.status_code == 200
    assert res_land.json()["total"] == 1
    assert res_land.json()["items"][0]["business_name"] == "Landline Only Clinic"

    # Filter whatsapp: should match only item3 (count = 1)
    res_wa = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?must_have_whatsapp=true")
    assert res_wa.status_code == 200
    assert res_wa.json()["total"] == 1
    assert res_wa.json()["items"][0]["business_name"] == "WhatsApp Clinic"

    # Filter exclude_already_saved: should match items 1, 2, 4 (count = 3)
    res_unsaved = auth_client.get(f"/api/v1/discovery/jobs/{job.id}/preview?exclude_already_saved=true")
    assert res_unsaved.status_code == 200
    assert res_unsaved.json()["total"] == 3
    names_unsaved = [it["business_name"] for it in res_unsaved.json()["items"]]
    assert "WhatsApp Clinic" not in names_unsaved


def test_live_sqlite_database_schema_and_zero_state():
    """
    Directly checks the SQLite production database 'india_leads.db' to confirm
    it is initialized, integrity check passes, reference data is preserved,
    and zero saved leads exist in the clean state.
    """
    import os
    # Project root D:\india-leads-platform\india_leads.db
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "india_leads.db")
    if not os.path.exists(db_path):
        pytest.skip("india_leads.db file not found at expected path")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify integrity
    cursor.execute("PRAGMA integrity_check;")
    assert cursor.fetchone()[0] == "ok"

    # Verify reference data is preserved
    cursor.execute("SELECT count(*) FROM india_locations;")
    assert cursor.fetchone()[0] == 30

    cursor.execute("SELECT count(*) FROM users;")
    assert cursor.fetchone()[0] >= 1

    # Verify zero saved leads in production database
    cursor.execute("SELECT count(*) FROM branches;")
    assert cursor.fetchone()[0] == 0

    cursor.execute("SELECT count(*) FROM companies;")
    assert cursor.fetchone()[0] == 0

    conn.close()
