import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    Company,
    Branch,
    BusinessContact,
    DuplicateCandidate,
    LeadSource
)
from app.services.deduplication.normalizer import DataNormalizer
from app.services.deduplication.matcher import BranchDeduplicationMatcher, MatchResult
from app.services.discovery.base import DiscoveredLeadItem


class DeduplicationResolver:
    def __init__(self, db: Session):
        self.db = db
        self.matcher = BranchDeduplicationMatcher(db)

    def process_discovered_lead(
        self,
        lead: DiscoveredLeadItem,
        org_id: str
    ) -> Tuple[Optional[Branch], str]:
        """
        Processes an incoming discovered lead through normalization, matching, and transactional upsert.
        Returns (branch, action_taken):
          action_taken in ["inserted", "updated", "flagged_duplicate", "rejected_license"]
        """
        # Sourcing compliance check: Only eligible records may be permanently stored
        if not lead.is_eligible_for_crm:
            return None, "rejected_license"

        match = self.matcher.evaluate_candidate(
            business_name=lead.business_name,
            city=lead.city,
            state=lead.state,
            locality=lead.locality,
            address_line=lead.address_line,
            pincode=lead.pincode,
            phone=lead.phone,
            website_url=lead.website_url,
            source_reference=lead.external_id,
            org_id=org_id
        )

        source = self.db.query(LeadSource).filter(LeadSource.code == lead.source_code).first()
        source_id = source.id if source else None

        # 1. Exact Duplicate -> Update existing branch
        if match.decision == MatchResult.EXACT_DUPLICATE and match.existing_branch_id:
            branch = self.db.query(Branch).filter(Branch.id == match.existing_branch_id).first()
            if branch:
                # Update missing fields
                if not branch.address_line and lead.address_line:
                    branch.address_line = lead.address_line
                if not branch.locality and lead.locality:
                    branch.locality = lead.locality
                if not branch.pincode and lead.pincode:
                    branch.pincode = lead.pincode
                if not branch.website_url and lead.website_url:
                    branch.website_url = lead.website_url
                branch.last_checked_at = datetime.now(timezone.utc)
                self.db.commit()
                return branch, "updated"

        # 2. Company resolution: find or create company
        norm_co_name = DataNormalizer.normalize_company_name(lead.business_name)
        company = None
        if match.existing_company_id:
            company = self.db.query(Company).filter(Company.id == match.existing_company_id).first()

        if not company:
            company = Company(
                organization_id=org_id,
                legal_name=lead.business_name.replace("[DEMO DATA]", "").strip(),
                normalized_name=norm_co_name,
                website_domain=DataNormalizer.normalize_domain(lead.website_url),
                primary_category=lead.category,
                description=f"Auto-registered from {lead.source_code}"
            )
            self.db.add(company)
            self.db.flush()

        # 3. Create new branch
        norm_branch_name = DataNormalizer.normalize_branch_name(lead.business_name)
        new_branch = Branch(
            company_id=company.id,
            branch_name=lead.business_name,
            normalized_branch_name=norm_branch_name,
            address_line=lead.address_line,
            locality=lead.locality,
            city=lead.city,
            state=lead.state,
            pincode=lead.pincode,
            country="India",
            website_url=lead.website_url,
            source_id=source_id,
            source_reference=lead.external_id,
            source_permission_status=lead.license_status,
            confidence_score=lead.raw_payload.get("confidence", 1.0) if lead.raw_payload else 1.0,
            enrichment_status="pending" if lead.website_url else "completed",
            is_demo=lead.is_demo,
            is_active=True
        )
        self.db.add(new_branch)
        self.db.flush()

        # Add initial phone contact if available
        if lead.phone:
            digits = "".join(ch for ch in lead.phone if ch.isdigit() or ch == '+')
            norm_phone = digits if digits.startswith("+91") else (f"+91{digits}" if len(digits) == 10 else digits)
            contact = BusinessContact(
                branch_id=new_branch.id,
                contact_type="mobile" if norm_phone.startswith("+919") or norm_phone.startswith("+918") or norm_phone.startswith("+917") or norm_phone.startswith("+916") else "landline",
                original_value=lead.phone,
                normalized_value=norm_phone,
                is_primary=True,
                is_verified=False,
                source=lead.source_code
            )
            self.db.add(contact)

        # 4. If uncertain match, create a DuplicateCandidate review entry
        if match.decision == MatchResult.UNCERTAIN_MATCH and match.existing_branch_id:
            candidate_entry = DuplicateCandidate(
                existing_branch_id=match.existing_branch_id,
                candidate_branch_id=new_branch.id,
                match_score=match.confidence_score,
                match_reasons=json.dumps(match.reasons),
                status="pending_review"
            )
            self.db.add(candidate_entry)
            self.db.commit()
            return new_branch, "flagged_duplicate"

        self.db.commit()
        return new_branch, "inserted"

    def resolve_candidate(
        self,
        candidate_id: str,
        resolution: str,
        user_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Manually resolves an uncertain duplicate match from the Duplicates Review dashboard.
        resolution: "merge" | "keep_distinct" | "reject_candidate"
        """
        record = self.db.query(DuplicateCandidate).filter(DuplicateCandidate.id == candidate_id).first()
        if not record:
            return False

        record.resolved_by_user_id = user_id
        record.resolution_notes = notes

        if resolution == "merge":
            # Transfer contacts and deactivate candidate branch
            candidate_branch = self.db.query(Branch).filter(Branch.id == record.candidate_branch_id).first()
            if candidate_branch:
                for c in candidate_branch.contacts:
                    c.branch_id = record.existing_branch_id
                candidate_branch.is_active = False
            record.status = "resolved_merged"

        elif resolution == "keep_distinct":
            record.status = "confirmed_distinct"

        elif resolution == "reject_candidate":
            candidate_branch = self.db.query(Branch).filter(Branch.id == record.candidate_branch_id).first()
            if candidate_branch:
                candidate_branch.is_active = False
            record.status = "confirmed_duplicate"

        self.db.commit()
        return True

