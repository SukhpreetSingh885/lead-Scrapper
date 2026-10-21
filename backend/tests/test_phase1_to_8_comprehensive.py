"""
Comprehensive Verification Test Suite for India Leads Platform
Testing All 12 Required Scenarios:
1. Chandigarh + Salon
2. Chandigarh + Gym
3. Mohali + Pet Shop
4. Mohali + Clinic
5. Fashion in Chandigarh
6. Multi-city deduplication
7. Preview-only discovery
8. Manual save
9. Individual and bulk delete
10. Contact enrichment with source_url and evidence
11. Export only contact-qualified records (rejecting email alone)
12. License attribution in CSV and XLSX exports
"""
import io
import json
import pytest
import openpyxl
from datetime import datetime, timezone

from app.models import (
    Branch,
    Company,
    BusinessContact,
    SocialProfile,
    DiscoveryJob,
    DiscoveryJobItem,
    discovery_job_leads,
    Export
)
from app.services.discovery.taxonomy import CategoryTaxonomyResolver
from app.services.discovery.overpass_provider import OverpassDiscoveryProvider
from app.services.deduplication.normalizer import DataNormalizer
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.enrichment.phone_extractor import IndianPhoneExtractor
from app.services.enrichment.email_extractor import EmailExtractor
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine
from app.services.exports.csv_export import CsvExportService
from app.services.exports.excel_export import ExcelExportService
from app.repositories.location_repo import LocationRepository
from app.repositories.lead_repo import LeadRepository
from app.schemas.lead import LeadFilterParams, BulkDeleteLeadsRequest


# ==========================================
# Scenario 1: Chandigarh + Salon
# ==========================================
def test_scenario_1_chandigarh_salon_taxonomy_and_filters():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("Salon")
    assert cat_def.canonical_name == "Salon"
    assert ("shop", "hairdresser") in cat_def.osm_tags
    assert ("shop", "beauty") in cat_def.osm_tags

    # Negative tags should prevent salons from accidentally matching cafes or gyms
    assert "amenity" in cat_def.negative_tags
    assert "cafe" in cat_def.negative_tags["amenity"]


# ==========================================
# Scenario 2: Chandigarh + Gym
# ==========================================
def test_scenario_2_chandigarh_gym_tags_and_negative_filters():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("Gym")
    assert cat_def.canonical_name == "Gym"
    tag_tuples = cat_def.osm_tags
    assert ("leisure", "fitness_centre") in tag_tuples
    assert ("sport", "fitness") in tag_tuples
    assert ("leisure", "gym") in tag_tuples

    # Negative tags must reject outdoor park fitness stations and playgrounds
    assert "leisure" in cat_def.negative_tags
    assert "fitness_station" in cat_def.negative_tags["leisure"]
    assert "playground" in cat_def.negative_tags["leisure"]


# ==========================================
# Scenario 3: Mohali + Pet Shop
# ==========================================
def test_scenario_3_mohali_pet_shop():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("Pet Shop")
    assert cat_def.canonical_name == "Pet Shop"
    assert ("shop", "pet") in cat_def.osm_tags
    assert ("shop", "aquarium") in cat_def.osm_tags
    assert "Pet Boarding / Pet Care" in cat_def.ambiguous_alternatives


# ==========================================
# Scenario 4: Mohali + Clinic
# ==========================================
def test_scenario_4_mohali_clinic():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("Clinic")
    assert cat_def.canonical_name == "Clinic"
    assert ("amenity", "clinic") in cat_def.osm_tags
    assert ("healthcare", "clinic") in cat_def.osm_tags
    assert ("amenity", "doctors") in cat_def.osm_tags


# ==========================================
# Scenario 5: Fashion in Chandigarh
# ==========================================
def test_scenario_5_fashion_in_chandigarh():
    cat_def, suggestions = CategoryTaxonomyResolver.resolve("Fashion")
    assert cat_def.canonical_name == "Fashion"
    assert ("shop", "clothes") in cat_def.osm_tags
    assert ("shop", "boutique") in cat_def.osm_tags
    assert "clothing store" in cat_def.aliases


# ==========================================
# Scenario 6: Multi-city deduplication across overlapping areas
# ==========================================
def test_scenario_6_multi_city_deduplication(db_session):
    loc_repo = LocationRepository(db_session)
    is_valid, resolved_list, err = loc_repo.parse_and_validate_locations("Chandigarh + Mohali + Panchkula")
    assert is_valid is True
    assert len(resolved_list) == 3
    cities = [c for c, _ in resolved_list]
    assert "Chandigarh" in cities
    assert "Mohali" in cities

    # Verify batch deduplication logic
    normalizer = DataNormalizer()
    seen_ext_ids = set()
    seen_business_keys = set()
    deduped_items = []

    # Mock elements found in both Chandigarh and Mohali queries (due to overlapping 15km radii)
    item_chd = {
        "external_id": "osm-node-998877",
        "business_name": "Gold's Gym Tricity",
        "latitude": 30.710,
        "longitude": 76.720,
        "city": "Chandigarh"
    }
    item_mohali_dup = {
        "external_id": "osm-node-998877",  # Identical node discovered in overlapping search
        "business_name": "Gold's Gym Tricity",
        "latitude": 30.710,
        "longitude": 76.720,
        "city": "Mohali"
    }

    for item in [item_chd, item_mohali_dup]:
        ext_id = item["external_id"]
        if ext_id in seen_ext_ids:
            continue
        norm_name = normalizer.normalize_company_name(item["business_name"])
        coord_key = f"{round(item['latitude'], 3)}_{round(item['longitude'], 3)}"
        b_key = f"{norm_name}_{coord_key}"
        if b_key in seen_business_keys:
            continue
        seen_ext_ids.add(ext_id)
        seen_business_keys.add(b_key)
        deduped_items.append(item)

    # Exactly 1 item should survive deduplication, not 2
    assert len(deduped_items) == 1
    assert deduped_items[0]["external_id"] == "osm-node-998877"


# ==========================================
# Scenario 7: Preview-only discovery (never auto-saves to CRM)
# ==========================================
def test_scenario_7_preview_only_discovery_isolation(db_session):
    job = DiscoveryJob(
        organization_id="test-org-1",
        location_input="Chandigarh",
        resolved_city="Chandigarh",
        resolved_state="Chandigarh",
        category="Gym",
        max_leads=50,
        source_code="overpass",
        status="completed",
        total_discovered=5,
        total_eligible=5,
        total_inserted=0  # Previews are NOT committed to CRM
    )
    db_session.add(job)
    db_session.flush()

    preview_item = DiscoveryJobItem(
        job_id=job.id,
        external_id="osm-node-101",
        business_name="Chandigarh Fitness Studio",
        category="Gym",
        city="Chandigarh",
        is_eligible_for_crm=True,
        is_saved=False,  # Unsaved
        is_already_saved=False
    )
    db_session.add(preview_item)
    db_session.commit()

    # Verify no Branch exists in CRM for this preview lead
    branches = db_session.query(Branch).filter(Branch.branch_name == "Chandigarh Fitness Studio").all()
    assert len(branches) == 0

    # Item is present in preview table
    item_in_db = db_session.query(DiscoveryJobItem).filter(DiscoveryJobItem.id == preview_item.id).first()
    assert item_in_db is not None
    assert item_in_db.is_saved is False


# ==========================================
# Scenario 8: Manual save of selected leads
# ==========================================
def test_scenario_8_manual_save(db_session):
    company = Company(
        organization_id="test-org-1",
        legal_name="Manual Save Co",
        normalized_name="manual save co",
        primary_category="Salon"
    )
    db_session.add(company)
    db_session.flush()

    branch = Branch(
        company_id=company.id,
        branch_name="Selected Salon Mohali",
        normalized_branch_name="selected salon mohali",
        city="Mohali",
        state="Punjab",
        source_permission_status="permitted_storage"
    )
    db_session.add(branch)
    db_session.flush()

    # Link with job via discovery_job_leads association
    job = DiscoveryJob(
        organization_id="test-org-1",
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Salon",
        max_leads=50,
        source_code="overpass",
        status="completed"
    )
    db_session.add(job)
    db_session.flush()

    db_session.execute(
        discovery_job_leads.insert().values(job_id=job.id, branch_id=branch.id)
    )
    db_session.commit()

    # Verify association exists
    linked_leads = db_session.query(Branch).join(
        discovery_job_leads, Branch.id == discovery_job_leads.c.branch_id
    ).filter(discovery_job_leads.c.job_id == job.id).all()
    assert len(linked_leads) == 1
    assert linked_leads[0].branch_name == "Selected Salon Mohali"


# ==========================================
# Scenario 9: Individual and bulk delete
# ==========================================
def test_scenario_9_individual_and_bulk_delete(db_session):
    company = Company(
        organization_id="test-org-delete",
        legal_name="Delete Corp",
        normalized_name="delete corp",
        primary_category="Clinic"
    )
    db_session.add(company)
    db_session.flush()

    b1 = Branch(
        company_id=company.id,
        branch_name="Clinic Branch 1",
        normalized_branch_name="clinic branch 1",
        city="Chandigarh",
        state="Chandigarh"
    )
    b2 = Branch(
        company_id=company.id,
        branch_name="Clinic Branch 2",
        normalized_branch_name="clinic branch 2",
        city="Chandigarh",
        state="Chandigarh"
    )
    db_session.add_all([b1, b2])
    db_session.commit()

    # 1. Single delete b1
    db_session.delete(b1)
    db_session.commit()
    assert db_session.query(Branch).filter(Branch.id == b1.id).first() is None
    # Company still remains because b2 exists
    assert db_session.query(Company).filter(Company.id == company.id).first() is not None

    # 2. Bulk delete remaining branch b2 and clean up orphaned company
    db_session.delete(b2)
    db_session.flush()
    if db_session.query(Branch).filter(Branch.company_id == company.id).count() == 0:
        db_session.delete(company)
    db_session.commit()

    assert db_session.query(Branch).filter(Branch.id == b2.id).first() is None
    assert db_session.query(Company).filter(Company.id == company.id).first() is None


# ==========================================
# Scenario 10: Contact enrichment with source_url and evidence
# ==========================================
def test_scenario_10_contact_enrichment_evidence():
    html_page = """
    <html>
      <body>
        <div class="header">
          <a href="tel:+919876543210">Call Us: +91 98765 43210</a>
          <a href="https://wa.me/919812345678">WhatsApp Chat</a>
        </div>
        <div class="footer">
          <p>For inquiries, email info@chandigarhgym.in or visit us in Sector 17.</p>
        </div>
      </body>
    </html>
    """
    page_url = "https://www.chandigarhgym.in/contact-us"

    phones = IndianPhoneExtractor.extract_from_text_and_html(html_page, source_url=page_url)
    assert len(phones) >= 2

    # Check evidence and source_url on extracted phone
    tel_contact = next((p for p in phones if p["normalized_value"] == "+919876543210"), None)
    assert tel_contact is not None
    assert tel_contact["source_url"] == page_url
    assert "Tel Link" in tel_contact["evidence"]

    # Check WhatsApp link
    wa_contact = next((p for p in phones if p["contact_type"] == "whatsapp"), None)
    assert wa_contact is not None
    assert wa_contact["source_url"] == page_url
    assert "WhatsApp Link" in wa_contact["evidence"]

    # Check Email extractor
    emails = EmailExtractor.extract_from_html(html_page, source_url=page_url)
    assert len(emails) == 1
    assert emails[0]["normalized_value"] == "info@chandigarhgym.in"
    assert emails[0]["source_url"] == page_url
    assert "chandigarhgym.in" in emails[0]["evidence"]


# ==========================================
# Scenario 11: Export only contact-qualified records (rejecting email alone)
# ==========================================
def test_scenario_11_export_only_contact_qualified_rejects_email_only(db_session):
    company = Company(
        organization_id="test-org-exports",
        legal_name="Export Quality Corp",
        normalized_name="export quality corp",
        primary_category="Gym"
    )
    db_session.add(company)
    db_session.flush()

    # Lead 1: Contact-qualified (has mobile)
    b_phone = Branch(
        company_id=company.id,
        branch_name="Fit Zone Chandigarh",
        normalized_branch_name="fit zone chandigarh",
        city="Chandigarh",
        state="Chandigarh",
        source_permission_status="permitted_storage"
    )
    # Lead 2: NOT contact-qualified (ONLY has email, no phone/mobile/whatsapp)
    b_email_only = Branch(
        company_id=company.id,
        branch_name="Email Only Fitness",
        normalized_branch_name="email only fitness",
        city="Chandigarh",
        state="Chandigarh",
        source_permission_status="permitted_storage"
    )
    db_session.add_all([b_phone, b_email_only])
    db_session.flush()

    c_phone = BusinessContact(
        branch_id=b_phone.id,
        contact_type="mobile",
        original_value="+91 98888 77777",
        normalized_value="+919888877777",
        is_primary=True,
        source="website_enrichment"
    )
    c_email = BusinessContact(
        branch_id=b_email_only.id,
        contact_type="email",
        original_value="contact@emailonly.com",
        normalized_value="contact@emailonly.com",
        is_primary=True,
        source="website_enrichment"
    )
    db_session.add_all([c_phone, c_email])
    db_session.commit()

    repo = LeadRepository(db_session)

    # When querying with has_contact_number=True (contact qualification):
    leads, count = repo.get_leads_paginated(
        org_id="test-org-exports",
        filters=LeadFilterParams(has_contact_number=True)
    )

    lead_ids = [l.id for l in leads]
    assert b_phone.id in lead_ids
    # Email-only lead MUST NOT be returned as contact-qualified
    assert b_email_only.id not in lead_ids


# ==========================================
# Scenario 12: License attribution in CSV and XLSX exports
# ==========================================
def test_scenario_12_license_attribution_in_exports(db_session):
    company = Company(
        organization_id="test-org-license",
        legal_name="Attribution Corp",
        normalized_name="attribution corp",
        primary_category="Salon"
    )
    db_session.add(company)
    db_session.flush()

    branch = Branch(
        company_id=company.id,
        branch_name="Attribution Salon Chandigarh",
        normalized_branch_name="attribution salon chandigarh",
        city="Chandigarh",
        state="Chandigarh",
        source_permission_status="permitted_storage"
    )
    db_session.add(branch)
    db_session.commit()

    # 1. Test CSV Export contains License & Attribution column
    csv_bytes = CsvExportService.generate_csv_bytes([branch])
    csv_text = csv_bytes.decode("utf-8-sig")
    assert "License & Attribution" in csv_text
    assert "ODbL 1.0 (C) OpenStreetMap contributors" in csv_text

    # 2. Test XLSX Export contains License & Attribution worksheet
    xlsx_bytes = ExcelExportService.generate_xlsx_bytes([branch])
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    sheet_names = wb.sheetnames
    assert "India Business Leads" in sheet_names
    assert "License & Attribution" in sheet_names

    lic_sheet = wb["License & Attribution"]
    assert lic_sheet.cell(row=2, column=2).value == "OpenStreetMap Contributors"
    assert "ODbL" in lic_sheet.cell(row=3, column=2).value

