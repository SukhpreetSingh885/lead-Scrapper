import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload

from app.models import DuplicateCandidate, Branch, Company
from app.schemas.duplicate import DuplicateCandidateOut
from app.repositories.lead_repo import LeadRepository


class DuplicateRepository:
    def __init__(self, db: Session):
        self.db = db
        self.lead_repo = LeadRepository(db)

    def get_pending_duplicates_paginated(
        self,
        org_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DuplicateCandidateOut], int]:
        query = self.db.query(DuplicateCandidate).options(
            joinedload(DuplicateCandidate.existing_branch).joinedload(Branch.company),
            joinedload(DuplicateCandidate.candidate_branch).joinedload(Branch.company),
        ).filter(DuplicateCandidate.status == "pending_review")

        if org_id:
            query = query.join(Branch, DuplicateCandidate.existing_branch_id == Branch.id).join(Company, Branch.company_id == Company.id).filter(Company.organization_id == org_id)

        total = query.count()
        offset = (page - 1) * page_size
        records = query.order_by(DuplicateCandidate.created_at.desc()).offset(offset).limit(page_size).all()

        output = []
        for r in records:
            reasons = []
            try:
                reasons = json.loads(r.match_reasons)
            except Exception:
                reasons = [r.match_reasons]

            existing_item = self.lead_repo._branch_to_list_item(r.existing_branch) if r.existing_branch else None
            candidate_item = self.lead_repo._branch_to_list_item(r.candidate_branch) if r.candidate_branch else None

            output.append(
                DuplicateCandidateOut(
                    id=r.id,
                    existing_branch_id=r.existing_branch_id,
                    candidate_branch_id=r.candidate_branch_id,
                    match_score=r.match_score,
                    match_reasons=reasons,
                    status=r.status,
                    existing_branch=existing_item,
                    candidate_branch=candidate_item,
                    resolution_notes=r.resolution_notes,
                    created_at=r.created_at
                )
            )

        return output, total

