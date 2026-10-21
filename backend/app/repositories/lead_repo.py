from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func

from app.core.config import settings
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
            is_archived=getattr(branch, "is_archived", False),
            archive_reason=getattr(branch, "archive_reason", None),
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
                    source=c.source,
                    source_url=getattr(c, "source_url", None),
                    evidence=getattr(c, "evidence", None)
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
            is_archived=getattr(branch, "is_archived", False),
            archive_reason=getattr(branch, "archive_reason", None),
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

        # Job isolation filter
        if filters and filters.job_id:
            from app.models.job import discovery_job_leads
            query = query.join(discovery_job_leads, Branch.id == discovery_job_leads.c.branch_id).filter(
                discovery_job_leads.c.job_id == filters.job_id
            )

        # By default exclude archived records
        if filters and filters.is_archived is not None:
            query = query.filter(Branch.is_archived == filters.is_archived)
        else:
            query = query.filter(Branch.is_archived == False)

        # If not in demo mode, exclude demo leads
        if filters and filters.is_demo is not None:
            query = query.filter(Branch.is_demo == filters.is_demo)
        elif not getattr(settings, "DEMO_MODE", False):
            query = query.filter(Branch.is_demo == False)

        if org_id:
            query = query.filter(Company.organization_id == org_id)

        if filters:
            if filters.city:
                query = query.filter(Branch.city.ilike(f"%{filters.city.strip()}%"))
            if filters.state:
                query = query.filter(Branch.state.ilike(f"%{filters.state.strip()}%"))
            if filters.category:
                cat_str = filters.category.strip()
                try:
                    from app.services.discovery.taxonomy import CategoryTaxonomyResolver
                    resolved, _ = CategoryTaxonomyResolver.resolve(cat_str)
                    target_cats = [cat_str, resolved.canonical_name]
                    query = query.filter(Company.primary_category.in_(target_cats))
                except Exception:
                    query = query.filter(Company.primary_category.ilike(f"%{cat_str}%"))
            if filters.enrichment_status:
                query = query.filter(Branch.enrichment_status == filters.enrichment_status)

            if filters.has_website:
                query = query.filter(Branch.website_url.isnot(None), Branch.website_url != "")

            # Contact qualification: has at least one valid business phone/mobile/whatsapp
            if filters.has_contact_number:
                query = query.filter(
                    Branch.contacts.any(BusinessContact.contact_type.in_(["mobile", "landline", "phone", "whatsapp"]))
                )

            if filters.has_mobile:
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "mobile"))
            if filters.has_whatsapp:
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "whatsapp"))
            if filters.has_phone and not filters.has_mobile:
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type.in_(["mobile", "landline", "phone"])))
            if filters.has_email:
                query = query.filter(Branch.contacts.any(BusinessContact.contact_type == "email"))

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

    def get_lead_by_id(self, lead_id: str, org_id: Optional[str] = None) -> Optional[LeadBranchDetail]:
        query = self.db.query(Branch).join(Company).options(
            joinedload(Branch.company),
            joinedload(Branch.contacts),
            joinedload(Branch.social_profiles),
            joinedload(Branch.source)
        ).filter(Branch.id == lead_id)

        if org_id:
            query = query.filter(Company.organization_id == org_id)

        branch = query.first()

        if not branch:
            return None
        return self._branch_to_detail(branch)

    def get_lead_ids_by_filters(
        self,
        org_id: Optional[str] = None,
        filters: Optional[LeadFilterParams] = None
    ) -> List[str]:
        query = self.db.query(Branch.id).join(Company).filter(
            Branch.is_active == True,
            Branch.is_archived == False
        )
        if not getattr(settings, "DEMO_MODE", False):
            query = query.filter(Branch.is_demo == False)

        if org_id:
            query = query.filter(Company.organization_id == org_id)

        if filters:
            if filters.job_id:
                from app.models.job import discovery_job_leads
                query = query.join(discovery_job_leads, Branch.id == discovery_job_leads.c.branch_id).filter(
                    discovery_job_leads.c.job_id == filters.job_id
                )
            if filters.city:
                query = query.filter(Branch.city.ilike(f"%{filters.city.strip()}%"))
            if filters.state:
                query = query.filter(Branch.state.ilike(f"%{filters.state.strip()}%"))
            if filters.category:
                cat_str = filters.category.strip()
                try:
                    from app.services.discovery.taxonomy import CategoryTaxonomyResolver
                    resolved, _ = CategoryTaxonomyResolver.resolve(cat_str)
                    target_cats = [cat_str, resolved.canonical_name]
                    query = query.filter(Company.primary_category.in_(target_cats))
                except Exception:
                    query = query.filter(Company.primary_category.ilike(f"%{cat_str}%"))
            if filters.has_contact_number:
                query = query.filter(
                    Branch.contacts.any(BusinessContact.contact_type.in_(["mobile", "landline", "phone", "whatsapp"]))
                )
            if filters.query:
                search_term = f"%{filters.query.strip()}%"
                query = query.filter(
                    or_(
                        Branch.branch_name.ilike(search_term),
                        Branch.address_line.ilike(search_term),
                        Branch.city.ilike(search_term),
                        Company.legal_name.ilike(search_term),
                        Branch.contacts.any(BusinessContact.normalized_value.ilike(search_term))
                    )
                )

        return [r[0] for r in query.all()]

    def get_dashboard_metrics(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        base_branch = self.db.query(Branch).join(Company).filter(
            Branch.is_active == True,
            Branch.is_archived == False
        )
        if not getattr(settings, "DEMO_MODE", False):
            base_branch = base_branch.filter(Branch.is_demo == False)

        if org_id:
            base_branch = base_branch.filter(Company.organization_id == org_id)

        total_unique_leads = base_branch.count()

        leads_with_mobile = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "mobile")
        ).count()

        leads_with_phone = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type.in_(["landline", "phone"]))
        ).count()

        leads_with_whatsapp = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "whatsapp")
        ).count()

        leads_with_email = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type == "email")
        ).count()

        leads_with_website = base_branch.filter(
            Branch.website_url.isnot(None),
            Branch.website_url != ""
        ).count()

        export_eligible_leads = base_branch.filter(
            Branch.contacts.any(BusinessContact.contact_type.in_(["mobile", "landline", "phone", "whatsapp"]))
        ).count()

        leads_missing_contacts = max(0, total_unique_leads - export_eligible_leads)

        dup_query = self.db.query(DuplicateCandidate).filter(
            DuplicateCandidate.status == "pending_review"
        )
        active_jobs_query = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.status.in_(["pending", "queued", "running"])
        )
        completed_jobs_query = self.db.query(DiscoveryJob).filter(
            DiscoveryJob.status.in_(["completed", "partially_completed"])
        )

        if org_id:
            dup_query = dup_query.join(Branch, DuplicateCandidate.existing_branch_id == Branch.id).join(Company, Branch.company_id == Company.id).filter(Company.organization_id == org_id)
            active_jobs_query = active_jobs_query.filter(DiscoveryJob.organization_id == org_id)
            completed_jobs_query = completed_jobs_query.filter(DiscoveryJob.organization_id == org_id)

        duplicate_candidates_count = dup_query.count()
        active_jobs = active_jobs_query.count()
        completed_jobs = completed_jobs_query.count()

        demo_leads_count = self.db.query(Branch).filter(Branch.is_demo == True).count()

        return {
            "total_unique_leads": total_unique_leads,
            "total_saved_leads": total_unique_leads,
            "leads_with_mobile": leads_with_mobile,
            "leads_with_phone": leads_with_phone,
            "leads_with_whatsapp": leads_with_whatsapp,
            "leads_with_email": leads_with_email,
            "leads_with_website": leads_with_website,
            "export_eligible_leads": export_eligible_leads,
            "leads_missing_contacts": leads_missing_contacts,
            "duplicate_candidates": duplicate_candidates_count,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "demo_leads_count": demo_leads_count,
            "live_leads_count": total_unique_leads,
            "is_demo_mode_active": getattr(settings, "DEMO_MODE", False)
        }

