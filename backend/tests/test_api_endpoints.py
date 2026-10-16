import pytest


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "India Leads Platform"
    assert data["free_testing_mode"]["enabled"] is True


def test_api_locations_suggest(client):
    response = client.get("/api/v1/locations?q=Mohali")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["city"] == "Mohali"


def test_api_discovery_job_creation_and_execution(client):
    # Valid Indian location
    payload = {
        "location": "Mohali",
        "category": "Salon",
        "max_leads": 10,
        "source": "demo_fixture"
    }
    response = client.post("/api/v1/discovery/jobs", json=payload)
    assert response.status_code == 201
    job = response.json()
    assert job["resolved_city"] == "Mohali"
    assert job["category"] == "Salon"
    assert job["status"] in ("completed", "running", "pending")
    assert job["total_discovered"] >= 1

    # Verify leads were inserted in DB
    leads_res = client.get("/api/v1/leads?city=Mohali")
    assert leads_res.status_code == 200
    leads_data = leads_res.json()
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

