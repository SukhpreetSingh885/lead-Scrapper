from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.models import (
    Branch,
    Company,
    BusinessContact,
    SocialProfile,
    LeadSource,
    DiscoveryJob,
    DuplicateCandidate,
)
from app.schemas.lead import LeadListItem, LeadBranchDetail, BusinessContactOut, SocialProfileOut, LeadFilterParams


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def _branch_to_list_item(self, branch: Branch) -> LeadListItem:
        mobile = None
        landline = None
        whatsapp = None
        email = None

        for c in branch.contacts:
            if c.contact_type == "mobile" and not mobile:
                mobile = c.normalized_value or c.original_value
            elif c.contact_type in ("landline", "phone") and not landline:
                landline = c.normalized_value or c.original_value
            elif c.contact_type == "whatsapp" and not whatsapp:
                whatsapp = c.normalized_value or c.original_value
            elif c.contact_type == "email" and not email:
                email = c.normalized_value or c.original_value

        return LeadListItem(
            id=branch.id,
            company_id=branch.company_id,
            business_name=branch.branch_name,
            category=branch.company.primary_category if branch.company else "Not Available",
            primary_mobile=mobile,
            primary_landline=landline,
            primary_whatsapp=whatsapp,
            primary_email=email,
            website_url=branch.website_url,
            city=branch.city,
            state=branch.state,
            locality=branch.locality,
            pincode=branch.pincode,
            address_line=branch.address_line,
            enrichment_status=branch.enrichment_status,
            source_name=branch.source.name if branch.source else "Independently Sourced",
            is_demo=branch.is_demo,
            social_profiles_count=len(branch.social_profiles),
            created_at=branch.created_at,
            updated_at=branch.updated_at
        )

    def _branch_to_detail(self, branch: Branch) -> LeadBranchDetail:
        mobile = None
        landline = None
        whatsapp = None
        email = None

        contacts_out = []
        for c in branch.contacts:
            if c.contact_type == "mobile" and not mobile:
                mobile = c.normalized_value or c.original_value
            elif c.contact_type in ("landline", "phone") and not landline:
                landline = c.normalized_value or c.original_value
            elif c.contact_type == "whatsapp" and not whatsapp:
                whatsapp = c.normalized_value or c.original_value
            elif c.contact_type == "email" and not email:
                email = c.normalized_value or c.original_value

            contacts_out.append(
                BusinessContactOut(
                    id=c.id,
                    contact_type=c.contact_type,
                    original_value=c.original_value,
                    normalized_value=c.normalized_value,
                    is_primary=c.is_primary,
                    is_verified=c.is_verified,
                    source=c.source
                )
            )

        socials_out = [
            SocialProfileOut(
                id=s.id,
                platform=s.platform,
                profile_url=s.profile_url,
                handle=s.handle
            ) for s in branch.social_profiles
        ]

        return LeadBranchDetail(
            id=branch.id,
            company_id=branch.company_id,
            business_name=branch.branch_name,
            legal_name=branch.company.legal_name if branch.company else branch.branch_name,
            category=branch.company.primary_category if branch.company else "Not Available",
            description=branch.company.description if branch.company else None,
            website_domain=branch.company.website_domain if branch.company else None,
            website_url=branch.website_url,
            address_line=branch.address_line,
            locality=branch.locality,
            city=branch.city,
            district=branch.district,
            state=branch.state,
            pincode=branch.pincode,
            country=branch.country,
            latitude=branch.latitude,
            longitude=branch.longitude,
            primary_mobile=mobile,
            primary_landline=landline,
            primary_whatsapp=whatsapp,
            primary_email=email,
            contacts=contacts_out,
            social_profiles=socials_out,
            source_name=branch.source.name if branch.source else "Independently Sourced",
            source_code=branch.source.code if branch.source else None,
            source_permission_status=branch.source_permission_status,
            confidence_score=branch.confidence_score,
            enrichment_status=branch.enrichment_status,
            last_checked_at=branch.last_checked_at,
            is_demo=branch.is_demo,
            created_at=branch.created_at,
            updated_at=branch.updated_at
        )

    def get_leads_paginated(
        self,
        org_id: Optional[str] = None,
        filters: Optional[LeadFilterParams] = None
    ) -> Tuple[List[LeadListItem], int]:
        query = self.db.query(Branch).join(Company).options(
            joinedload(Branch.company),
            joinedload(Branch.contacts),
            joinedload(Branch.social_profiles),
            joinedload(Branch.source)
        ).filter(Branch.is_active == True)

        if org_id:
            query = query.filter(Company.organization_id == org_id)

        if filters:
            if filters.city:
                query = query.filter(Branch.city.ilike(f"%{filters.city.strip()}%"))
            if filters.state:
                query = query.filter(Branch.state.ilike(f"%{filters.state.strip()}%"))
            if filters.category:
                query = query.filter(Company.primary_category.ilike(f"%{filters.category.strip()}%"))
            if filters.enrichment_status:
                query = query.filter(Branch.enrichment_status == filters.enrichment_status)
            if filters.is_demo is not None:
                query = query.filter(Branch.is_demo == filters.is_demo)

            if filters.has_website:
                query = query.filter(Branch.website_url.isnot(None), Branch.website_url != "")

            if filters.has_phone or filters.has_mobile or filters.has_email or filters.has_whatsapp:
                contact_types = []
                if filters.has_mobile:
                    contact_types.append("mobile")
                if filters.has_phone and "mobile" not in contact_types:
                    contact_types.extend(["mobile", "landline", "phone"])
                if filters.has_email:
                    contact_types.append("email")
                if filters.has_whatsapp:
                    contact_types.append("whatsapp")

                if contact_types:
                    query = query.filter(
                        Branch.contacts.any(BusinessContact.contact_type.in_(contact_types))
                    )

            if filters.query:
                search_term = f"%{filters.query.strip()}%"
                query = query.filter(
                    or_(
                        Branch.branch_name.ilike(search_term),
                        Branch.address_line.ilike(search_term),
                        Branch.city.ilike(search_term),
                        Branch.locality.ilike(search_term),
                        Company.legal_name.ilike(search_term),
                        Branch.contacts.any(BusinessContact.normalized_value.ilike(search_term))
                    )
                )

        total = query.count()

        page = filters.page if filters else 1
        page_size = filters.page_size if filters else 25
        offset = (page - 1) * page_size

        branches = query.order_by(Branch.created_at.desc()).offset(offset).limit(page_size).all()
        items = [self._branch_to_list_item(b) for b in branches]
        return items, total

    def get_lead_by_id(self, lead_id: str) -> Optional[LeadBranchDetail]:
        branch = self.db.query(Branch).options(
            joinedload(Branch.company),
            joinedload(Branch.contacts),
            joinedload(Branch.social_profiles),
            joinedload(Branch.source)
        ).filter(Branch.id == lead_id).first()

        if not branch:
            return None
        return self._branch_to_detail(branch)

    def get_dashboard_metrics(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        base_branch = self.db.query(Branch).join(Company).filter(Branch.is_active == True)
        if org_id:
            base_branch = base_branch.filter(Company.organization_id == org_id)

        total_unique_leads = base_branch.count()

        leads_with_mobile = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "mobile")
        ).count()

        leads_with_email = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "email")
        ).count()

        leads_with_website = base_branch.filter(
            Branch.website_url.isnot(None),
            Branch.website_url != ""
        ).count()

        leads_with_whatsapp = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "whatsapp")
        ).count()

        duplicate_candidates_count = self.db.query(DuplicateCandidate).filter(
            DuplicateCandidate.status == "pending_review"
        ).count()

        active_jobs = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.status.in_(["pending", "queued", "running"])
        ).count()

        completed_jobs = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.status.in_(["completed", "partially_completed"])
        ).count()

        demo_leads_count = base_branch.filter(Branch.is_demo == True).count()

        return {
            "total_unique_leads": total_unique_leads,
            "leads_with_mobile": leads_with_mobile,
            "leads_with_email": leads_with_email,
            "leads_with_website": leads_with_website,
            "leads_with_whatsapp": leads_with_whatsapp,
            "duplicate_candidates": duplicate_candidates_count,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "demo_leads_count": demo_leads_count,
            "live_leads_count": total_unique_leads - demo_leads_count,
            "is_demo_mode_active": demo_leads_count > 0
        }

