import pytest
from app.services.discovery.taxonomy import CategoryTaxonomyResolver, TAXONOMY
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.models import Branch, Company, BusinessContact, DiscoveryJob, DiscoveryJobItem


def test_chandigarh_gym_taxonomy_and_tags():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("GYM")
    assert cat_def.canonical_name == "Gym"
    
    # Check that gym OSM tags include accurate, relevant tags
    osm_tag_keys = [t[0] for t in cat_def.osm_tags]
    osm_tag_vals = [t[1] for t in cat_def.osm_tags]
    assert "fitness_centre" in osm_tag_vals
    assert "fitness" in osm_tag_vals
    assert "gym" in osm_tag_vals
    
    # Check negative tags exclude cafes, salons, restaurants
    assert "cafe" in cat_def.negative_tags.get("amenity", [])
    assert "restaurant" in cat_def.negative_tags.get("amenity", [])
    assert "hairdresser" in cat_def.negative_tags.get("shop", [])


def test_chandigarh_location_resolution():
    provider = OverpassDiscoveryProvider()
    lat, lon, city, state = provider._resolve_coordinates("Chandigarh")
    assert round(lat, 2) == 30.73
    assert round(lon, 2) == 76.78
    assert city == "Chandigarh"
    assert state == "Chandigarh"


def test_validate_element_category_gym_precision():
    provider = OverpassDiscoveryProvider()
    
    # Valid fitness centre
    valid_gym, cat = provider._validate_element_category(
        {"name": "Gold's Gym", "leisure": "fitness_centre"}, "Gym"
    )
    assert valid_gym is True
    assert cat == "Gym"

    # Valid gym with sport=fitness
    valid_fit, cat = provider._validate_element_category(
        {"name": "Atlantic Fitness", "sport": "fitness", "leisure": "fitness_centre"}, "Gym"
    )
    assert valid_fit is True
    assert cat == "Gym"

    # Sports hall with gym in name
    valid_hall, cat = provider._validate_element_category(
        {"name": "Ultimate Fitness", "leisure": "sports_hall"}, "Gym"
    )
    assert valid_hall is True
    assert cat == "Gym"

    # Multi-value semicolon sport tag (e.g. Hammer Gym)
    valid_semicolon, cat = provider._validate_element_category(
        {"name": "Iron Gym", "sport": "fitness;exercise"}, "Gym"
    )
    assert valid_semicolon is True
    assert cat == "Gym"

    # Rejects outdoor park fitness station (non-commercial)
    invalid_station, _ = provider._validate_element_category(
        {"name": "Sector 10 Park Fitness Station", "leisure": "fitness_station", "sport": "fitness"}, "Gym"
    )
    assert invalid_station is False

    # Rejects cafe
    invalid_cafe, _ = provider._validate_element_category(
        {"name": "Blue Tokai Coffee", "amenity": "cafe"}, "Gym"
    )
    assert invalid_cafe is False

    # Rejects salon
    invalid_salon, _ = provider._validate_element_category(
        {"name": "Looks Salon", "shop": "hairdresser"}, "Gym"
    )
    assert invalid_salon is False

    # Rejects sports centre without fitness (e.g. swimming pool)
    invalid_pool, _ = provider._validate_element_category(
        {"name": "Raina Swimming Pool", "leisure": "sports_centre", "sport": "swimming"}, "Gym"
    )
    assert invalid_pool is False


def test_preview_mode_and_contact_qualification(client, db_session):
    # Search Chandigarh + Gym
    payload = {
        "location": "Chandigarh",
        "category": "Gym",
        "max_leads": 500,
        "source": "overpass"
    }
    res = client.post("/api/v1/discovery/jobs", json=payload)
    assert res.status_code == 201
    job_data = res.json()
    job_id = job_data["id"]

    # In async/BackgroundTasks mode, fetch the finalized job status
    job_get = client.get(f"/api/v1/discovery/jobs/{job_id}")
    assert job_get.status_code == 200
    job_data = job_get.json()

    assert job_data["status"] == "completed"
    assert job_data["total_discovered"] >= 6
    assert job_data["total_eligible"] >= 6
    assert job_data["total_contact_qualified"] >= 1
    # Preview isolation: 0 inserted to CRM
    assert job_data["total_inserted"] == 0

    # Verify preview storage holds items
    preview_res = client.get(f"/api/v1/discovery/jobs/{job_id}/preview")
    assert preview_res.status_code == 200
    pdata = preview_res.json()
    items = pdata["items"]
    assert len(items) >= 6

    # Verify that businesses with missing phone numbers are NOT rejected
    missing_phone_items = [it for it in items if not it["phone"] and not it["mobile"]]
    assert len(missing_phone_items) > 0  # Still present in preview!

    # Verify CRM has zero leads before manual save
    crm_res = client.get(f"/api/v1/leads?city=Chandigarh&category=Gym")
    assert crm_res.status_code == 200
    assert crm_res.json()["total"] == 0

    # Save a single selected lead
    target_item = items[0]
    save_res = client.post("/api/v1/leads/save-selected", json={
        "job_id": job_id,
        "item_ids": [target_item["id"]]
    })
    assert save_res.status_code == 200
    sdata = save_res.json()
    assert sdata["saved_count"] == 1

    # Verify lead is now in CRM
    crm_after = client.get(f"/api/v1/leads?city=Chandigarh&category=Gym")
    assert crm_after.json()["total"] == 1

    # Save same lead again -> deduplication verification (already_existing_count == 1, saved_count == 0)
    save_dup_res = client.post("/api/v1/leads/save-selected", json={
        "job_id": job_id,
        "item_ids": [target_item["id"]]
    })
    assert save_dup_res.status_code == 200
    dup_data = save_dup_res.json()
    assert dup_data["already_existing_count"] == 1
    assert dup_data["saved_count"] == 0

    # Delete the saved lead
    saved_lead_id = sdata["saved_lead_ids"][0]
    del_res = client.delete(f"/api/v1/leads/{saved_lead_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Lead deleted successfully."

    # Verify lead is gone from CRM
    crm_final = client.get(f"/api/v1/leads?city=Chandigarh&category=Gym")
    assert crm_final.json()["total"] == 0


def test_radius_search_configuration():
    provider = OverpassDiscoveryProvider()
    
    # Verify 10km radius query
    q10 = provider._build_overpass_query(
        tag_filters=[("leisure", "fitness_centre")],
        lat=30.7333,
        lon=76.7794,
        radius_meters=10000
    )
    assert "around:10000,30.7333,76.7794" in q10

    # Verify 25km radius query
    q25 = provider._build_overpass_query(
        tag_filters=[("leisure", "fitness_centre")],
        lat=30.7333,
        lon=76.7794,
        radius_meters=25000
    )
    assert "around:25000,30.7333,76.7794" in q25


@pytest.mark.asyncio
async def test_overpass_error_distinction_and_zero_results(monkeypatch):
    import httpx
    provider = OverpassDiscoveryProvider()

    # Case 1: Genuine 0 results (HTTP 200 with empty elements list)
    class Mock200EmptyResponse:
        status_code = 200
        def json(self):
            return {"elements": []}

    class MockClientEmpty:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, *args, **kwargs):
            return Mock200EmptyResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockClientEmpty())
    results = await provider.search("Chandigarh", "Gym", max_results=50)
    # Must NOT raise false rate limit error; should return empty list
    assert results == []

    # Case 2: Rate limit (HTTP 429) across mirrors
    class Mock429Response:
        status_code = 429
        text = "Too many requests"

    class MockClient429:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, *args, **kwargs):
            return Mock429Response()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockClient429())
    with pytest.raises(RuntimeError) as exc_info:
        await provider.search("Chandigarh", "Gym", max_results=50)
    assert "rate limit reached (HTTP 429)" in str(exc_info.value)


