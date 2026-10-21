import pytest
import csv
import io
import openpyxl
from app.models import Branch, Company, DiscoveryJob
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.exports.csv_export import CsvExportService
from app.services.exports.excel_export import ExcelExportService


@pytest.mark.asyncio
async def test_live_overpass_mohali_salon_discovery_and_export(db_session):
    """
    Primary Objective Test:
    Location: Mohali
    Category: Salon
    Maximum Leads: 50
    """
    provider = OverpassDiscoveryProvider()
    db = db_session

    # 1. Execute Overpass search for Mohali + Salon
    leads = await provider.search(
        location="Mohali",
        category="Salon",
        max_results=50
    )

    assert len(leads) >= 4, f"Expected at least 4 real business leads, got {len(leads)}"

    # Check discovered business names
    names = [item.business_name for item in leads]
    assert any("Castle Bloom" in n for n in names)
    assert any("TRIMMING" in n or "London" in n or "Ali" in n or "Simrat" in n or "Barberia" in n for n in names)

    # Check provenance and eligibility
    for item in leads:
        assert item.source_code == "overpass"
        assert item.is_demo is False
        assert item.is_eligible_for_crm is True
        assert item.country == "India"
        assert item.latitude is not None
        assert item.longitude is not None

    # Check social URL classification: Ali's Masters should have Instagram in social_profiles and website_url None
    ali_leads = [item for item in leads if "Ali" in item.business_name]
    if ali_leads:
        ali = ali_leads[0]
        assert ali.website_url is None
        assert ali.social_profiles is not None
        assert "instagram" in ali.social_profiles

    # Check Castle Bloom has real business website
    castle_leads = [item for item in leads if "Castle Bloom" in item.business_name]
    if castle_leads:
        castle = castle_leads[0]
        assert castle.website_url == "http://www.castlebloom.com/"

    # 2. Process through DeduplicationResolver into database
    resolver = DeduplicationResolver(db)
    saved_branches = []
    for item in leads:
        branch, action = resolver.process_discovered_lead(item, org_id="test-org-1")
        if branch:
            saved_branches.append(branch)

    assert len(saved_branches) >= 4

    # Verify branches in DB are real and not archived
    for b in saved_branches:
        assert b.is_demo is False
        assert b.is_archived is False
        assert b.source_reference.startswith("osm-")

    # 3. Test CSV Export: Must contain real leads and NO demo leads
    csv_bytes = CsvExportService.generate_csv_bytes(saved_branches)
    assert len(csv_bytes) > 0
    csv_text = csv_bytes.decode("utf-8-sig")
    assert "Castle Bloom" in csv_text
    assert "[DEMO DATA]" not in csv_text

    # 4. Test Excel Export: Must generate valid XLSX
    xlsx_bytes = ExcelExportService.generate_xlsx_bytes(saved_branches)
    assert len(xlsx_bytes) > 0
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    ws = wb.active
    assert ws.title == "India Business Leads"
    assert ws.max_row >= 5  # Header + at least 4 rows
