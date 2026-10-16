from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class SocialProfile(Base, TimestampMixin):
    __tablename__ = "social_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # facebook, instagram, linkedin, youtube, twitter_x, other
    profile_url = Column(String(500), nullable=False)
    original_url = Column(String(500), nullable=True)
    handle = Column(String(100), nullable=True)

    branch = relationship("Branch", back_populates="social_profiles")

    __table_args__ = (
        Index("idx_social_branch_platform", "branch_id", "platform", "profile_url", unique=True),
    )

