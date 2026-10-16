import pytest
from app.services.enrichment.phone_extractor import IndianPhoneExtractor


def test_indian_mobile_normalization_equivalence():
    """
    Requirements Section 6:
    9876543210, +91 98765 43210, 091-9876543210 should normalize to the same E.164 number (+919876543210).
    """
    equivalent_inputs = [
        "9876543210",
        "+91 98765 43210",
        "091-9876543210",
        "+91-98765-43210",
        "+919876543210",
        "98765 43210"
    ]

    expected_e164 = "+919876543210"

    for raw in equivalent_inputs:
        res = IndianPhoneExtractor.normalize_phone(raw)
        assert res is not None, f"Failed to normalize valid Indian phone: {raw}"
        assert res["normalized_value"] == expected_e164
        assert res["contact_type"] == "mobile"
        assert res["is_valid"] is True


def test_indian_landline_normalization():
    """Test landline with STD codes (e.g. Mohali/Chandigarh 0172-2214567, Delhi 011-23344556)."""
    # 0172 is Mohali/Chandigarh STD code
    res = IndianPhoneExtractor.normalize_phone("0172-2214567")
    assert res is not None
    assert res["normalized_value"] == "+911722214567"
    assert res["contact_type"] in ("landline", "phone")


def test_reject_invalid_phone_numbers():
    invalid_inputs = [
        "",
        "   ",
        "12345",
        "0000000000",
        "1111111111",
        "abcdefghij",
        "98765",
        "+1 555-123-4567",  # US phone - reject non-Indian
    ]

    for raw in invalid_inputs:
        res = IndianPhoneExtractor.normalize_phone(raw)
        if res:
            # If phonenumbers parses it as US, verify it's not +91
            assert not res["normalized_value"].startswith("+91")
        else:
            assert res is None

