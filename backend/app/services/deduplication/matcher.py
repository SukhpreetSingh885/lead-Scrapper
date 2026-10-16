import json
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from app.models import Branch, Company, BusinessContact
from app.services.deduplication.normalizer import DataNormalizer


class MatchResult:
    EXACT_DUPLICATE = "exact_duplicate"
    NEW_BRANCH_SAME_COMPANY = "new_branch_same_company"
    UNCERTAIN_MATCH = "uncertain_match"
    NEW_ENTITY = "new_entity"

    def __init__(
        self,
        decision: str,
        confidence_score: float,
        reasons: List[str],
        existing_branch_id: Optional[str] = None,
        existing_company_id: Optional[str] = None
    ):
        self.decision = decision
        self.confidence_score = confidence_score
        self.reasons = reasons
        self.existing_branch_id = existing_branch_id
        self.existing_company_id = existing_company_id


class BranchDeduplicationMatcher:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_candidate(
        self,
        business_name: str,
        city: str,
        state: str,
        locality: Optional[str] = None,
        address_line: Optional[str] = None,
        pincode: Optional[str] = None,
        phone: Optional[str] = None,
        website_url: Optional[str] = None,
        source_reference: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> MatchResult:
        """
        Executes multi-stage duplicate evaluation across the entire database.
        """
        norm_co_name = DataNormalizer.normalize_company_name(business_name)
        norm_branch_name = DataNormalizer.normalize_branch_name(business_name)
        norm_address = DataNormalizer.normalize_address(address_line)
        norm_pincode = DataNormalizer.normalize_pincode(pincode)
        norm_domain = DataNormalizer.normalize_domain(website_url)
        clean_city = city.strip().lower()

        # =====================================================================
        # STAGE 2: DETERMINISTIC MATCHING
        # =====================================================================

        # 1. Match by exact source_reference (e.g. Place ID or unique licensed ID)
        if source_reference:
            exact_ref = self.db.query(Branch).filter(
                Branch.source_reference == source_reference
            ).first()
            if exact_ref:
                return MatchResult(
                    decision=MatchResult.EXACT_DUPLICATE,
                    confidence_score=1.0,
                    reasons=[f"Exact source reference match: {source_reference}"],
                    existing_branch_id=exact_ref.id,
                    existing_company_id=exact_ref.company_id
                )

        # Query candidates in the same city or matching company domain
        query = self.db.query(Branch).join(Company)
        if org_id:
            query = query.filter(Company.organization_id == org_id)

        city_candidates = query.filter(Branch.city.ilike(f"%{clean_city}%")).all()

        # Check for same company presence in this city or database
        matching_company = None
        for cand in city_candidates:
            if cand.company.normalized_name == norm_co_name:
                matching_company = cand.company
                break
            if norm_domain and cand.company.website_domain == norm_domain:
                matching_company = cand.company
                break

        # If not found in city, check broader company query
        if not matching_company and norm_domain:
            matching_company = self.db.query(Company).filter(
                Company.website_domain == norm_domain
            ).first()

        # Check branches of matching company
        if matching_company:
            for branch in matching_company.branches:
                # 2. Exact branch name + same city
                if branch.normalized_branch_name == norm_branch_name and branch.city.lower() == clean_city:
                    return MatchResult(
                        decision=MatchResult.EXACT_DUPLICATE,
                        confidence_score=1.0,
                        reasons=["Exact company identity and normalized branch name match in same city."],
                        existing_branch_id=branch.id,
                        existing_company_id=matching_company.id
                    )

                # 3. Same address line + same city
                if norm_address and branch.address_line:
                    existing_norm_addr = DataNormalizer.normalize_address(branch.address_line)
                    if existing_norm_addr == norm_address and branch.city.lower() == clean_city:
                        return MatchResult(
                            decision=MatchResult.EXACT_DUPLICATE,
                            confidence_score=0.98,
                            reasons=["Exact company match and identical normalized street address."],
                            existing_branch_id=branch.id,
                            existing_company_id=matching_company.id
                        )

                # 4. Same locality & PIN code
                if locality and branch.locality:
                    if locality.lower().strip() == branch.locality.lower().strip() and branch.city.lower() == clean_city:
                        name_sim = fuzz.token_sort_ratio(norm_co_name, branch.company.normalized_name)
                        if name_sim >= 90:
                            return MatchResult(
                                decision=MatchResult.EXACT_DUPLICATE,
                                confidence_score=0.95,
                                reasons=[f"Matching company ({name_sim}%), same city ({city}), and same locality ({locality})."],
                                existing_branch_id=branch.id,
                                existing_company_id=matching_company.id
                            )

                # 5. Distinct branch detection (e.g. Phase 7 vs Phase 3B2)
                # If company matches, but localities/addresses are distinctly different,
                # this is explicitly a NEW BRANCH of the same company!
                if locality and branch.locality:
                    loc1 = locality.lower().strip()
                    loc2 = branch.locality.lower().strip()
                    if loc1 != loc2 and fuzz.token_sort_ratio(loc1, loc2) < 60:
                        return MatchResult(
                            decision=MatchResult.NEW_BRANCH_SAME_COMPANY,
                            confidence_score=0.95,
                            reasons=[f"Recognized company with distinct branch location: '{locality}' vs existing '{branch.locality}'."],
                            existing_company_id=matching_company.id
                        )

        # =====================================================================
        # STAGE 3: FUZZY MATCHING (RapidFuzz / pg_trgm logic)
        # =====================================================================
        highest_score = 0.0
        best_candidate: Optional[Branch] = None
        match_signals: List[str] = []

        for cand in city_candidates:
            # Score company name similarity
            name_score = fuzz.token_set_ratio(norm_co_name, cand.company.normalized_name)
            addr_score = 0
            if norm_address and cand.address_line:
                addr_score = fuzz.token_set_ratio(norm_address, DataNormalizer.normalize_address(cand.address_line))

            locality_match = bool(
                locality and cand.locality and
                fuzz.token_sort_ratio(locality.lower(), cand.locality.lower()) > 80
            )

            pincode_match = bool(
                norm_pincode and cand.pincode and
                norm_pincode == DataNormalizer.normalize_pincode(cand.pincode)
            )

            # Combined weighted confidence
            weights = 0.0
            total_points = 0.0

            weights += 0.5
            total_points += (name_score / 100.0) * 0.5

            if norm_address and cand.address_line:
                weights += 0.3
                total_points += (addr_score / 100.0) * 0.3

            if locality and cand.locality:
                weights += 0.1
                total_points += (1.0 if locality_match else 0.0) * 0.1

            if norm_pincode and cand.pincode:
                weights += 0.1
                total_points += (1.0 if pincode_match else 0.0) * 0.1

            confidence = total_points / weights if weights > 0 else 0.0

            if confidence > highest_score:
                highest_score = confidence
                best_candidate = cand
                match_signals = [
                    f"Name similarity: {name_score:.1f}%",
                    f"Address similarity: {addr_score:.1f}%",
                    f"Same Locality: {locality_match}",
                    f"Same Pincode: {pincode_match}"
                ]

        # STAGE 4: RESOLUTION
        if highest_score >= 0.88 and best_candidate:
            return MatchResult(
                decision=MatchResult.EXACT_DUPLICATE,
                confidence_score=highest_score,
                reasons=[f"High-confidence fuzzy duplicate ({highest_score*100:.1f}%): " + ", ".join(match_signals)],
                existing_branch_id=best_candidate.id,
                existing_company_id=best_candidate.company_id
            )
        elif highest_score >= 0.70 and best_candidate:
            return MatchResult(
                decision=MatchResult.UNCERTAIN_MATCH,
                confidence_score=highest_score,
                reasons=[f"Uncertain duplicate match ({highest_score*100:.1f}%). Requires review: " + ", ".join(match_signals)],
                existing_branch_id=best_candidate.id,
                existing_company_id=best_candidate.company_id
            )

        return MatchResult(
            decision=MatchResult.NEW_ENTITY,
            confidence_score=1.0,
            reasons=["No duplicate branch or company found in database."],
            existing_company_id=matching_company.id if matching_company else None
        )

