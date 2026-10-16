from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_name = Column(String(255), nullable=False)
    normalized_branch_name = Column(String(255), nullable=False, index=True)
    address_line = Column(String(500), nullable=True)
    locality = Column(String(255), nullable=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), nullable=True, index=True)
    country = Column(String(50), default="India", nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    website_url = Column(String(500), nullable=True)

    is_headquarters = Column(Boolean, default=False, nullable=False)
    source_id = Column(String(36), ForeignKey("lead_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    source_reference = Column(String(255), nullable=True)
    source_permission_status = Column(String(50), default="permitted_storage", nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    enrichment_status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed, not_applicable
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    company = relationship("Company", back_populates="branches")
    source = relationship("LeadSource", back_populates="branches")
    contacts = relationship("BusinessContact", back_populates="branch", cascade="all, delete-orphan")
    social_profiles = relationship("SocialProfile", back_populates="branch", cascade="all, delete-orphan")
    enrichment_jobs = relationship("EnrichmentJob", back_populates="branch", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_branch_city_pincode", "city", "pincode"),
        Index("idx_branch_norm_city", "normalized_branch_name", "city"),
    )

