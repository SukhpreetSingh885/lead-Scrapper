import pytest
import json
from unittest.mock import patch, AsyncMock
from app.models import Branch, Company, BusinessContact, DiscoveryJob, DiscoveryJobItem, User, Organization
from app.services.enrichment.phone_extractor import IndianPhoneExtractor
from app.services.enrichment.website_enricher import WebsiteEnrichmentEngine
from app.services.deduplication.resolver import DeduplicationResolver
from app.schemas.lead import SaveSelectedLeadsRequest
from app.api.v1.endpoints.leads import save_selected_leads
from app.workers.tasks.export_tasks import execute_export_generation
from app.models.export import Export


def test_phone_extractor_multi_numbers_and_classification():
    """Requirement 2, 3, 4: Parse multi-numbers, STD landlines, and Indian mobiles."""
    # 1. Comma/semicolon delimited
    raw_multi = "+91 172 5044436; +91 99888 54440, 011-23344556"
    extracted = IndianPhoneExtractor.extract_multiple_phones(raw_multi)
    assert len(extracted) == 3

    by_type = {e["normalized_value"]: e["contact_type"] for e in extracted}
    assert by_type["+911725044436"] == "landline"
    assert by_type["+919988854440"] == "mobile"
    assert by_type["+911123344556"] == "landline"

    # 2. Slashed extension
    slashed = "0172-5044436/37"
    extracted_slashed = IndianPhoneExtractor.extract_multiple_phones(slashed)
    assert len(extracted_slashed) == 2
    assert "+911725044436" in [e["normalized_value"] for e in extracted_slashed]
    assert "+911725044437" in [e["normalized_value"] for e in extracted_slashed]

    # 3. OSM Contact Tags
    tags = {
        "contact:mobile": "9988854440",
        "contact:phone": "0172-5044436",
        "contact:whatsapp": "+919988854440",
    }
    osm_contacts = IndianPhoneExtractor.extract_all_contacts_from_osm_tags(tags, elem_type="node", elem_id=9999)
    assert len(osm_contacts) >= 3
    types = [c["contact_type"] for c in osm_contacts]
    assert "mobile" in types
    assert "landline" in types
    assert "whatsapp" in types

    for c in osm_contacts:
        assert c["source"] == "osm"
        assert c["source_url"] == "https://www.openstreetmap.org/node/9999"
        assert "OSM tag:" in c["evidence"]


@pytest.mark.asyncio
async def test_preview_website_enrichment_no_crm_saving(db_session):
    """Requirement 5, 6, 7: Preview website enrichment runs and extracts contacts without saving to CRM."""
    db = db_session
    engine = WebsiteEnrichmentEngine(db)

    # Initial branch count
    initial_branches = db.query(Branch).count()
    initial_companies = db.query(Company).count()

    mock_html = """
    <html>
      <body>
        <h1>Dr. Sodhi Health Clinic</h1>
        <p>Book Appointment: <a href="tel:+918146677369">Call 81466-77369</a></p>
        <p>WhatsApp Desk: <a href="https://wa.me/918146677363">Chat on WhatsApp</a></p>
        <p>Reach us at contact@sodhihealthindia.com</p>
        <p>Office Landline: 0172-5094333</p>
      </body>
    </html>
    """

    with patch("app.services.enrichment.crawler.WebsiteCrawler.crawl_site", new_callable=AsyncMock) as mock_crawl:
        mock_crawl.return_value = {
            "https://www.sodhihealthindia.com/": mock_html,
            "https://www.sodhihealthindia.com/contact.php": mock_html,
        }

        result = await engine.enrich_preview_item("https://www.sodhihealthindia.com/", "Dr. Sodhi Health Clinic")

    assert result["success"] is True
    assert result["pages_crawled"] == 2

    extracted_phones = result["phones"]
    extracted_emails = result["emails"]

    assert len(extracted_phones) >= 3
    phone_vals = [p["normalized_value"] for p in extracted_phones]
    assert "+918146677369" in phone_vals
    assert "+918146677363" in phone_vals
    assert "+911725094333" in phone_vals

    # Check provenance
    for p in extracted_phones:
        assert p["source"] == "website_enrichment"
        assert "sodhihealthindia.com" in p["source_url"]
        assert p["evidence"] is not None

    email_vals = [e["normalized_value"] for e in extracted_emails]
    assert "contact@sodhihealthindia.com" in email_vals

    # Strictly verify NO CRM branches or companies were created
    assert db.query(Branch).count() == initial_branches
    assert db.query(Company).count() == initial_companies


@pytest.mark.asyncio
async def test_saving_preview_item_retains_all_extracted_contacts(db_session):
    """Requirement 9: Saving preview lead preserves all contacts (mobile, landline, whatsapp, email) with provenance."""
    db = db_session
    user = db.query(User).filter(User.id == "test-user-1").first()
    org = db.query(Organization).filter(Organization.id == "test-org-1").first()

    # 1. Create a discovery job with a preview item
    job = DiscoveryJob(
        organization_id=org.id,
        location_input="Mohali",
        resolved_city="Mohali",
        resolved_state="Punjab",
        category="Clinic",
        source_code="overpass",
        status="completed",
        total_discovered=1,
        total_eligible=1,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    all_contacts_payload = [
        {
            "original_value": "+91 81466 77369",
            "normalized_value": "+918146677369",
            "contact_type": "mobile",
            "is_valid": True,
            "source": "website_enrichment",
            "source_url": "https://www.sodhihealth.com/contact",
            "evidence": "Tel Link: tel:+918146677369"
        },
        {
            "original_value": "0172-5094333",
            "normalized_value": "+911725094333",
            "contact_type": "landline",
            "is_valid": True,
            "source": "osm",
            "source_url": "https://www.openstreetmap.org/node/12345",
            "evidence": "OSM tag: phone=0172-5094333"
        },
        {
            "original_value": "+91 81466 77363",
            "normalized_value": "+918146677363",
            "contact_type": "whatsapp",
            "is_valid": True,
            "source": "website_enrichment",
            "source_url": "https://www.sodhihealth.com/contact",
            "evidence": "WhatsApp Link: https://wa.me/918146677363"
        },
        {
            "original_value": "info@sodhihealth.com",
            "normalized_value": "info@sodhihealth.com",
            "contact_type": "email",
            "is_valid": True,
            "source": "website_enrichment",
            "source_url": "https://www.sodhihealth.com/contact",
            "evidence": "Mailto Link: info@sodhihealth.com"
        }
    ]

    raw_payload_dict = {
        "external_id": "test_preview_node_123",
        "business_name": "Sodhi Health Centre",
        "category": "Clinic",
        "city": "Mohali",
        "state": "Punjab",
        "phone": "+911725094333",
        "mobile": "+918146677369",
        "whatsapp": "+918146677363",
        "email": "info@sodhihealth.com",
        "website_url": "https://www.sodhihealth.com",
        "all_contacts": all_contacts_payload
    }

    job_item = DiscoveryJobItem(
        job_id=job.id,
        external_id="test_preview_node_123",
        raw_payload=json.dumps(raw_payload_dict),
        business_name="Sodhi Health Centre",
        category="Clinic",
        city="Mohali",
        state="Punjab",
        phone="+911725094333",
        mobile="+918146677369",
        whatsapp="+918146677363",
        email="info@sodhihealth.com",
        website="https://www.sodhihealth.com",
        source_code="overpass",
        is_eligible_for_crm=True,
        is_saved=False,
    )
    db.add(job_item)
    db.commit()
    db.refresh(job_item)

    # 2. Call save_selected_leads API endpoint
    req = SaveSelectedLeadsRequest(
        job_id=job.id,
        item_ids=[job_item.id],
        save_all_eligible=False
    )
    res = await save_selected_leads(req=req, current_user=user, db=db)

    assert res.success is True
    assert res.saved_count == 1

    # 3. Verify in database: All contacts retained with full provenance
    db.refresh(job_item)
    assert job_item.is_saved is True
    assert job_item.branch_id is not None

    contacts = db.query(BusinessContact).filter(BusinessContact.branch_id == job_item.branch_id).all()
    assert len(contacts) >= 4

    c_map = {(c.contact_type, c.normalized_value): c for c in contacts}
    assert ("mobile", "+918146677369") in c_map
    assert ("landline", "+911725094333") in c_map
    assert ("whatsapp", "+918146677363") in c_map
    assert ("email", "info@sodhihealth.com") in c_map

    mob_contact = c_map[("mobile", "+918146677369")]
    assert mob_contact.source == "website_enrichment"
    assert mob_contact.source_url == "https://www.sodhihealth.com/contact"
    assert "tel:+918146677369" in mob_contact.evidence

    osm_contact = c_map[("landline", "+911725094333")]
    assert osm_contact.source in ("osm", "overpass")


def test_export_strict_contact_qualification(db_session):
    """Requirement 10: Strict contact qualification rule excludes businesses missing all phones."""
    db = db_session
    org = db.query(Organization).filter(Organization.id == "test-org-1").first()

    # 1. Create company
    comp = Company(
        organization_id=org.id,
        legal_name="Test Enterprises",
        normalized_name="test enterprises",
        primary_category="Retail"
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)

    # Branch A: Has valid mobile
    b_valid = Branch(
        company_id=comp.id,
        branch_name="Branch with Mobile",
        normalized_branch_name="branch with mobile",
        city="Mohali",
        state="Punjab",
        country="India",
        is_active=True,
        is_archived=False,
        is_demo=False,
        source_permission_status="permitted_storage"
    )
    db.add(b_valid)
    db.commit()
    db.refresh(b_valid)

    c_mob = BusinessContact(
        branch_id=b_valid.id,
        contact_type="mobile",
        original_value="+91 99888 12345",
        normalized_value="+919988812345",
        is_primary=True,
        is_verified=True,
        source="osm"
    )
    db.add(c_mob)

    # Branch B: Has only email (no mobile, no landline, no whatsapp)
    b_no_phone = Branch(
        company_id=comp.id,
        branch_name="Branch with No Phone",
        normalized_branch_name="branch with no phone",
        city="Mohali",
        state="Punjab",
        country="India",
        is_active=True,
        is_archived=False,
        is_demo=False,
        source_permission_status="permitted_storage"
    )
    db.add(b_no_phone)
    db.commit()
    db.refresh(b_no_phone)

    c_email = BusinessContact(
        branch_id=b_no_phone.id,
        contact_type="email",
        original_value="contact@nophone.in",
        normalized_value="contact@nophone.in",
        is_primary=True,
        is_verified=True,
        source="osm"
    )
    db.add(c_email)
    db.commit()

    # 2. Trigger export
    export_rec = Export(
        organization_id=org.id,
        file_format="csv",
        filter_criteria=json.dumps({"city": "Mohali"}),
        status="pending",
        download_token="test_tok_123"
    )
    db.add(export_rec)
    db.commit()
    db.refresh(export_rec)

    execute_export_generation(export_rec.id)
    db.refresh(export_rec)

    assert export_rec.status == "ready"
    # Row count MUST only include b_valid (1 row), strictly excluding b_no_phone
    assert export_rec.row_count == 1
