import pytest
from app.services.discovery.licensed_import import LicensedImportService

SAMPLE_CSV = """Business Name,Category,Mobile,Phone,Email,Website,Address,Locality,City,State,PIN Code
Elite Styling Lounge,Salon,+91 98760 11223,0172-4011223,contact@elitemohali.in,https://elitemohali.in,SCO 10,Phase 7,Mohali,Punjab,160062
Urban Cuts,Barber,9988776655,,info@urbancuts.in,https://urbancuts.in,Booth 4,Sector 35,Chandigarh,Chandigarh,160035
""".encode("utf-8")


def test_licensed_csv_import_parsing():
    items = LicensedImportService.parse_csv(
        file_bytes=SAMPLE_CSV,
        license_name="Test B2B License 2026",
        permitted_usage="Permitted Storage & Enrichment"
    )

    assert len(items) == 2

    item1 = items[0]
    assert item1.business_name == "Elite Styling Lounge"
    assert item1.category == "Salon"
    assert item1.city == "Mohali"
    assert item1.state == "Punjab"
    assert item1.phone == "+91 98760 11223"
    assert item1.is_eligible_for_crm is True
    assert item1.license_status == "permitted_storage"
    assert item1.raw_payload["import_license"] == "Test B2B License 2026"

    item2 = items[1]
    assert item2.business_name == "Urban Cuts"
    assert item2.city == "Chandigarh"

