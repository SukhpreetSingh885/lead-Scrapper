import pytest
from app.repositories.location_repo import LocationRepository


def test_valid_indian_cities_resolution(db_session):
    repo = LocationRepository(db_session)

    # Mohali
    res = repo.validate_indian_location("Mohali")
    assert res.is_valid is True
    assert res.resolved_city == "Mohali"
    assert res.resolved_state == "Punjab"

    # Chandigarh
    res = repo.validate_indian_location("Chandigarh")
    assert res.is_valid is True
    assert res.resolved_city == "Chandigarh"

    # Bengaluru
    res = repo.validate_indian_location("Bengaluru")
    assert res.is_valid is True
    assert res.resolved_city == "Bengaluru"
    assert res.resolved_state == "Karnataka"

    # Jaipur
    res = repo.validate_indian_location("Jaipur")
    assert res.is_valid is True
    assert res.resolved_city == "Jaipur"


def test_valid_indian_pincode_resolution(db_session):
    repo = LocationRepository(db_session)

    # Mohali Phase 7 pincode
    res = repo.validate_indian_location("160062")
    assert res.is_valid is True
    assert res.resolved_city == "Mohali"
    assert res.resolved_pincode == "160062"

    # Bengaluru Koramangala pincode
    res = repo.validate_indian_location("560034")
    assert res.is_valid is True
    assert res.resolved_city == "Bengaluru"


def test_reject_non_indian_locations(db_session):
    repo = LocationRepository(db_session)

    foreign_locations = ["New York", "London", "Tokyo", "Sydney", "Paris", "Berlin"]
    for loc in foreign_locations:
        res = repo.validate_indian_location(loc)
        assert res.is_valid is False
        assert "not recognized as a valid location in India" in res.message


def test_location_autocomplete_suggestions(db_session):
    repo = LocationRepository(db_session)

    suggestions = repo.suggest_locations("Moh", limit=5)
    assert len(suggestions) >= 1
    assert any("Mohali" in s.city for s in suggestions)
    assert all("India" in s.display_name for s in suggestions)

