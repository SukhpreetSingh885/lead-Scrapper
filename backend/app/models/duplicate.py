from sqlalchemy import Column, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class DuplicateCandidate(Base, TimestampMixin):
    __tablename__ = "duplicate_candidates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    existing_branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False)
    match_reasons = Column(Text, nullable=False)  # JSON-encoded array of match signals
    status = Column(String(50), default="pending_review", nullable=False, index=True)  # pending_review, confirmed_duplicate, confirmed_distinct, resolved_merged
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    existing_branch = relationship("Branch", foreign_keys=[existing_branch_id])
    candidate_branch = relationship("Branch", foreign_keys=[candidate_branch_id])
    resolver = relationship("User", foreign_keys=[resolved_by_user_id])

    __table_args__ = (
        Index("idx_dup_pair", "existing_branch_id", "candidate_branch_id", unique=True),
    )

