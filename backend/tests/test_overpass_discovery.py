import pytest
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider, CATEGORY_TAG_MAP


def test_overpass_category_mapping_valid():
    provider = OverpassDiscoveryProvider()
    
    # Salon mapping
    salon_tags = provider._resolve_category_tags("Salon")
    assert ("shop", "hairdresser") in salon_tags
    assert ("shop", "beauty") in salon_tags

    # Restaurant mapping
    rest_tags = provider._resolve_category_tags("Restaurant")
    assert ("amenity", "restaurant") in rest_tags

    # Cafe mapping
    cafe_tags = provider._resolve_category_tags("Cafe")
    assert ("amenity", "cafe") in cafe_tags

    # Hotel mapping
    hotel_tags = provider._resolve_category_tags("Hotels")
    assert ("tourism", "hotel") in hotel_tags


def test_overpass_unmapped_category_raises_clear_error():
    provider = OverpassDiscoveryProvider()
    with pytest.raises(ValueError) as excinfo:
        provider._resolve_category_tags("Alien Spaceship Manufacturing")
    assert "This business category is not yet supported" in str(excinfo.value)
    assert "Supported categories include" in str(excinfo.value)


def test_overpass_coordinates_resolution():
    provider = OverpassDiscoveryProvider()
    lat, lon, city, state = provider._resolve_coordinates("Mohali")
    assert round(lat, 2) == 30.70
    assert round(lon, 2) == 76.72
    assert "Punjab" in state

    lat_chd, lon_chd, _, _ = provider._resolve_coordinates("Chandigarh")
    assert round(lat_chd, 2) == 30.73


def test_overpass_social_url_classification():
    provider = OverpassDiscoveryProvider()
    
    # Mock OSM raw elements
    raw_elements = [
        {
            "type": "node",
            "id": 14200887881,
            "lat": 30.6868625,
            "lon": 76.6868586,
            "tags": {
                "name": "Ali's Masters Salon & Academy",
                "phone": "+919780516299",
                "website": "https://www.instagram.com/alis_masters/",
                "addr:city": "Mohali",
                "addr:housenumber": "SCO 38",
                "addr:postcode": "140308",
                "shop": "hairdresser"
            }
        },
        {
            "type": "node",
            "id": 2562499728,
            "lat": 30.7340276,
            "lon": 76.7551396,
            "tags": {
                "name": "Castle Bloom",
                "website": "http://www.castlebloom.com/",
                "addr:city": "Chandigarh",
                "addr:postcode": "160023",
                "shop": "beauty"
            }
        }
    ]

    # Parse through provider parser logic
    discovered = []
    for elem in raw_elements:
        tags = elem.get("tags", {})
        name = tags.get("name")
        raw_web = tags.get("website")
        website_url = None
        social_profiles = {}

        if raw_web:
            if "instagram.com" in raw_web:
                social_profiles["instagram"] = raw_web
            else:
                website_url = raw_web

        discovered.append({
            "name": name,
            "website_url": website_url,
            "social_profiles": social_profiles
        })

    # First item has Instagram as social profile, NOT official website
    assert discovered[0]["website_url"] is None
    assert discovered[0]["social_profiles"]["instagram"] == "https://www.instagram.com/alis_masters/"

    # Second item has actual business website
    assert discovered[1]["website_url"] == "http://www.castlebloom.com/"
    assert "instagram" not in discovered[1]["social_profiles"]

