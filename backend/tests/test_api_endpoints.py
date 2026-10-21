import pytest


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "India Leads Platform"
    assert "enabled" in data["free_testing_mode"]
    assert "overpass" in data["live_providers"]


def test_api_locations_suggest(client):
    response = client.get("/api/v1/locations?q=Mohali")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["city"] == "Mohali"


def test_api_discovery_job_creation_and_execution(client):
    # Valid Indian location with Overpass provider
    payload = {
        "location": "Mohali",
        "category": "Salon",
        "max_leads": 10,
        "source": "overpass"
    }
    response = client.post("/api/v1/discovery/jobs", json=payload)
    assert response.status_code == 201
    job = response.json()
    assert job["resolved_city"] == "Mohali"
    assert job["category"] == "Salon"
    assert job["status"] in ("completed", "running", "pending")
    
    # In async/BackgroundTasks mode, fetch the finalized job status
    job_get = client.get(f"/api/v1/discovery/jobs/{job['id']}")
    assert job_get.status_code == 200
    final_job = job_get.json()
    assert final_job["total_discovered"] >= 1

    # Verify preview results exist in preview storage without auto-CRM saving
    preview_res = client.get(f"/api/v1/discovery/jobs/{job['id']}/preview")
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert len(preview_data["items"]) >= 1

    # Verify CRM has 0 leads before explicit user save (Preview Isolation)
    leads_res_before = client.get("/api/v1/leads?city=Mohali")
    assert leads_res_before.status_code == 200
    assert leads_res_before.json()["total"] == 0

    # User explicitly saves selected / eligible preview leads
    save_res = client.post("/api/v1/leads/save-selected", json={
        "job_id": job["id"],
        "save_all_eligible": True
    })
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["saved_count"] >= 1

    # Verify leads are now saved in CRM database
    leads_res_after = client.get("/api/v1/leads?city=Mohali")
    assert leads_res_after.status_code == 200
    leads_data = leads_res_after.json()
    assert leads_data["total"] >= 1


def test_api_discovery_job_rejects_foreign_location(client):
    payload = {
        "location": "New York",
        "category": "Salon",
        "max_leads": 10,
        "source": "demo_fixture"
    }
    response = client.post("/api/v1/discovery/jobs", json=payload)
    assert response.status_code == 400
    err = response.json()
    assert "not recognized as a valid location in India" in err["detail"]


def test_api_export_creation(client):
    payload = {
        "file_format": "csv",
        "city": "Mohali"
    }
    response = client.post("/api/v1/exports", json=payload)
    assert response.status_code == 201
    exp = response.json()
    assert exp["status"] in ("ready", "processing", "pending")
    assert exp["download_url"] is not None

