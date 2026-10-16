from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class DiscoveryJob(Base, TimestampMixin):
    __tablename__ = "discovery_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    location_input = Column(String(255), nullable=False)
    resolved_city = Column(String(100), nullable=False, index=True)
    resolved_state = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    max_leads = Column(Integer, default=50, nullable=False)
    source_code = Column(String(50), default="demo_fixture", nullable=False)
    filters_json = Column(Text, nullable=True)

    status = Column(String(50), default="pending", nullable=False, index=True)
    total_discovered = Column(Integer, default=0, nullable=False)
    total_eligible = Column(Integer, default=0, nullable=False)
    total_inserted = Column(Integer, default=0, nullable=False)
    total_updated = Column(Integer, default=0, nullable=False)
    total_duplicates_flagged = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="discovery_jobs")
    items = relationship("DiscoveryJobItem", back_populates="job", cascade="all, delete-orphan")


class DiscoveryJobItem(Base, TimestampMixin):
    __tablename__ = "discovery_job_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), nullable=True)
    raw_payload = Column(Text, nullable=True)
    business_name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    is_eligible_for_crm = Column(Boolean, default=False, nullable=False)
    rejection_reason = Column(String(255), nullable=True)

    job = relationship("DiscoveryJob", back_populates="items")


class EnrichmentJob(Base, TimestampMixin):
    __tablename__ = "enrichment_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)
    pages_crawled = Column(Integer, default=0, nullable=False)
    emails_found = Column(Integer, default=0, nullable=False)
    phones_found = Column(Integer, default=0, nullable=False)
    socials_found = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    branch = relationship("Branch", back_populates="enrichment_jobs")

