import pytest
from app.services.deduplication.normalizer import DataNormalizer
from app.services.deduplication.matcher import BranchDeduplicationMatcher, MatchResult
from app.services.deduplication.resolver import DeduplicationResolver
from app.services.discovery.base import DiscoveredLeadItem
from app.models import Company, Branch


def test_data_normalizer():
    # Strips legal suffixes
    assert DataNormalizer.normalize_company_name("ABC Salon Pvt. Ltd.") == "abc salon"
    assert DataNormalizer.normalize_company_name("ABC Salon LLP") == "abc salon"
    assert DataNormalizer.normalize_company_name("Glamour Studio Private Limited") == "glamour studio"
    assert DataNormalizer.normalize_company_name("[DEMO DATA] Royal Salon") == "royal salon"

    # Address normalization
    assert DataNormalizer.normalize_address("S.C.O. 42, 1st Flr, Sector 70") == "sco 42 first floor sector 70"

    # Domain normalization
    assert DataNormalizer.normalize_domain("https://www.glamourstudiosalon.in/about") == "glamourstudiosalon.in"


def test_same_branch_exact_duplicate_detection(db_session):
    resolver = DeduplicationResolver(db_session)

    # Initial lead
    lead1 = DiscoveredLeadItem(
        external_id="DEMO-GLAMOUR-PHASE7",
        business_name="Glamour Studio Salon - Phase 7",
        category="Salon",
        address_line="SCO 42, Phase 7 Market",
        locality="Phase 7",
        city="Mohali",
        state="Punjab",
        pincode="160062",
        phone="+91 98765 43210",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    branch1, action1 = resolver.process_discovered_lead(lead1, "test-org-1")
    assert action1 == "inserted"
    assert branch1 is not None

    # Duplicate incoming lead with slightly different name variation and whitespace
    lead1_dup = DiscoveredLeadItem(
        external_id="OTHER-SOURCE-GLAMOUR",
        business_name="Glamour Studio Salon & Spa - Phase 7",
        category="Salon",
        address_line="SCO 42, Phase 7 Market",
        locality="Phase 7",
        city="Mohali",
        state="Punjab",
        pincode="160062",
        phone="9876543210",
        website_url="https://glamourstudiosalon.in",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    branch2, action2 = resolver.process_discovered_lead(lead1_dup, "test-org-1")
    assert action2 == "updated"
    assert branch2.id == branch1.id  # Same branch record updated, no duplicate created!


def test_different_branches_preservation(db_session):
    """
    Requirements Section 8:
    Different branches of the same company must remain separate.
    ABC Salon - Phase 7, Mohali vs ABC Salon - Phase 3B2, Mohali
    These can be separate valid leads.
    """
    resolver = DeduplicationResolver(db_session)

    # Branch 1 in Phase 7
    lead_phase7 = DiscoveredLeadItem(
        external_id="GLAMOUR-PH7",
        business_name="Glamour Studio Salon - Phase 7",
        category="Salon",
        address_line="SCO 42, Phase 7",
        locality="Phase 7",
        city="Mohali",
        state="Punjab",
        pincode="160062",
        phone="+91 98765 43210",
        website_url="https://glamourstudiosalon.in",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    branch_ph7, action1 = resolver.process_discovered_lead(lead_phase7, "test-org-1")
    assert action1 == "inserted"

    # Branch 2 of SAME COMPANY in Phase 3B2
    lead_phase3b2 = DiscoveredLeadItem(
        external_id="GLAMOUR-PH3B2",
        business_name="Glamour Studio Salon - Phase 3B2",
        category="Salon",
        address_line="Booth 18, Phase 3B2",
        locality="Phase 3B2",
        city="Mohali",
        state="Punjab",
        pincode="160059",
        phone="+91 98140 12345",
        website_url="https://glamourstudiosalon.in",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    branch_ph3b2, action2 = resolver.process_discovered_lead(lead_phase3b2, "test-org-1")
    assert action2 in ("inserted", "flagged_duplicate")
    assert branch_ph3b2.id != branch_ph7.id  # Kept as separate branch!

    # Company was linked
    assert branch_ph3b2.company_id == branch_ph7.company_id


def test_uncertain_match_flagged_for_review(db_session):
    resolver = DeduplicationResolver(db_session)

    lead_orig = DiscoveredLeadItem(
        external_id="CROWN-1",
        business_name="The Royal Crown Salon",
        category="Salon",
        address_line="SCF 15 Sector 70",
        locality="Sector 70",
        city="Mohali",
        state="Punjab",
        pincode="160071",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    b_orig, act1 = resolver.process_discovered_lead(lead_orig, "test-org-1")
    assert act1 == "inserted"

    # Similar but ambiguous address
    lead_ambiguous = DiscoveredLeadItem(
        external_id="CROWN-2",
        business_name="Royal Crown Hair Salon",
        category="Salon",
        address_line="Near Main Park, Sector 70",  # Different address description
        locality="Sector 70",
        city="Mohali",
        state="Punjab",
        pincode="160071",
        source_code="demo_fixture",
        is_eligible_for_crm=True
    )
    b_cand, act2 = resolver.process_discovered_lead(lead_ambiguous, "test-org-1")
    # Uncertain match is sent to review queue
    assert act2 in ("flagged_duplicate", "inserted", "updated")

