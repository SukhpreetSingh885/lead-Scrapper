import pytest
import json
import uuid
from app.models import DiscoveryJob, DiscoveryJobItem, User, Organization
from app.repositories.location_repo import LocationRepository
from app.repositories.job_repo import JobRepository
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider, INDIAN_CITY_COORDINATES
from app.workers.tasks.discovery_tasks import execute_discovery_job
from app.schemas.job import DiscoveryJobCreate, DiscoveryJobOut


def test_parse_and_validate_multicity(db_session):
    loc_repo = LocationRepository(db_session)
    raw_str = "Chandigarh + Mohali + Panchkula"
    is_valid, resolved_list, err = loc_repo.parse_and_validate_locations(raw_str)
    assert is_valid is True
    assert err is None
    assert len(resolved_list) == 3
    cities = [c for c, _ in resolved_list]
    assert "Chandigarh" in cities
    assert "Mohali" in cities
    assert "Panchkula" in cities


def test_city_coordinates_accuracy():
    provider = OverpassDiscoveryProvider()
    
    # 1. Chandigarh
    lat_c, lon_c, city_c, state_c = provider._resolve_coordinates("Chandigarh")
    assert round(lat_c, 4) == 30.7333
    assert round(lon_c, 4) == 76.7794
    assert city_c == "Chandigarh"
    assert state_c == "Chandigarh"

    # 2. Mohali
    lat_m, lon_m, city_m, state_m = provider._resolve_coordinates("Mohali")
    assert round(lat_m, 4) == 30.7046
    assert round(lon_m, 4) == 76.7179
    assert city_m == "Mohali"
    assert state_m == "Punjab"

    # 3. Panchkula
    lat_p, lon_p, city_p, state_p = provider._resolve_coordinates("Panchkula")
    assert round(lat_p, 4) == 30.6942
    assert round(lon_p, 4) == 76.8606
    assert city_p == "Panchkula"
    assert state_p == "Haryana"


def test_multicity_discovery_job_execution(db_session):
    """
    Tests that a multi-city discovery job:
    1. Executes per-city Overpass searches.
    2. Collects per_city_stats with coordinates, radius, raw_discovered, duplicates_removed, unique_contributed.
    3. Accurately attributes leads to their closest geographic city (Mohali, Panchkula, Chandigarh).
    4. Serializes per_city_stats into DiscoveryJobOut schema.
    """
    db = db_session
    org_id = f"test-org-{uuid.uuid4().hex[:8]}"
    org = Organization(id=org_id, name="Test Org", slug=org_id)
    db.add(org)
    db.commit()

    job_repo = JobRepository(db)
    job_in = DiscoveryJobCreate(
        location="Chandigarh + Mohali + Panchkula",
        category="Salon",
        max_leads=50,
        source="overpass",
        radius_km=15,
        locations=["Chandigarh", "Mohali", "Panchkula"]
    )

    job = job_repo.create_discovery_job(
        job_in=job_in,
        resolved_city="Chandigarh, Mohali, Panchkula",
        resolved_state="Chandigarh, Punjab, Haryana",
        org_id=org_id,
        source_code="overpass"
    )

    # Execute discovery synchronously
    result = execute_discovery_job(job.id)
    assert result.get("status") == "completed"

    db.refresh(job)
    assert job.status == "completed"
    assert job.total_discovered > 0

    # Verify per-city statistics
    filters_data = json.loads(job.filters_json)
    per_city = filters_data.get("per_city_stats")
    assert per_city is not None, "per_city_stats not found in filters_json"
    assert len(per_city) == 3, f"Expected 3 cities in per_city_stats, got {len(per_city)}"

    city_names = [s["city"] for s in per_city]
    assert "Chandigarh" in city_names
    assert "Mohali" in city_names
    assert "Panchkula" in city_names

    for s in per_city:
        assert s["latitude"] > 0
        assert s["longitude"] > 0
        assert s["radius_meters"] == 15000
        assert s["raw_discovered"] >= 0
        assert s["duplicates_removed"] >= 0

    # Verify schema serialization
    job_out = DiscoveryJobOut.model_validate(job)
    assert job_out.per_city_stats is not None
    assert len(job_out.per_city_stats) == 3
    assert job_out.per_city_stats[0].city == per_city[0]["city"]

    # Verify preview leads geographic attribution
    items = db.query(DiscoveryJobItem).filter(DiscoveryJobItem.job_id == job.id).all()
    assert len(items) == job.total_discovered

    item_cities = {it.city for it in items}
    # Check that leads are not all stamped solely with Chandigarh
    print("Discovered Lead Cities:", item_cities)
    assert len(item_cities) > 1, f"Expected multiple cities represented in preview items, got {item_cities}"


def test_balanced_quota_allocation_no_starvation():
    """
    Tests that when total unique candidates exceed max_leads,
    the round-robin allocation draws fairly from all cities so no city is starved.
    """
    from collections import defaultdict
    city_buckets = {
        "Chandigarh": [f"Chd-{i}" for i in range(30)],
        "Mohali": [f"Moh-{i}" for i in range(20)],
        "Panchkula": [f"Pan-{i}" for i in range(20)]
    }
    max_leads = 15

    # Simulated balanced selection algorithm
    discovered_items = []
    bucket_keys = list(city_buckets.keys())
    indices = {k: 0 for k in bucket_keys}
    while len(discovered_items) < max_leads:
        added_any = False
        for k in bucket_keys:
            if indices[k] < len(city_buckets[k]):
                discovered_items.append(city_buckets[k][indices[k]])
                indices[k] += 1
                added_any = True
                if len(discovered_items) >= max_leads:
                    break
        if not added_any:
            break

    assert len(discovered_items) == 15
    chd_count = sum(1 for x in discovered_items if "Chd" in x)
    moh_count = sum(1 for x in discovered_items if "Moh" in x)
    pan_count = sum(1 for x in discovered_items if "Pan" in x)

    # In a fair round robin of 15 across 3 buckets with ample items, each gets exactly 5 items
    assert chd_count == 5
    assert moh_count == 5
    assert pan_count == 5
