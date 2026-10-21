import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, Index, Table
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


discovery_job_leads = Table(
    "discovery_job_leads",
    Base.metadata,
    Column("job_id", String(36), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("branch_id", String(36), ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


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
    total_contact_qualified = Column(Integer, default=0, nullable=False)
    total_inserted = Column(Integer, default=0, nullable=False)
    total_updated = Column(Integer, default=0, nullable=False)
    total_duplicates_flagged = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="discovery_jobs")
    items = relationship("DiscoveryJobItem", back_populates="job", cascade="all, delete-orphan")
    leads = relationship("Branch", secondary=discovery_job_leads, backref="discovery_jobs")

    @property
    def per_city_stats(self):
        if not self.filters_json:
            return None
        try:
            data = json.loads(self.filters_json)
            return data.get("per_city_stats")
        except Exception:
            return None

    @property
    def contact_metrics(self):
        if not self.filters_json:
            return {}
        try:
            return json.loads(self.filters_json).get("contact_metrics", {})
        except Exception:
            return {}

    @property
    def total_mobile(self) -> int:
        metrics = self.contact_metrics
        if "total_mobile" in metrics:
            return metrics["total_mobile"]
        if self.items:
            return sum(1 for it in self.items if bool(it.mobile))
        return 0

    @property
    def total_landline(self) -> int:
        metrics = self.contact_metrics
        if "total_landline" in metrics:
            return metrics["total_landline"]
        if self.items:
            return sum(1 for it in self.items if bool(it.phone and it.phone != it.mobile))
        return 0

    @property
    def total_whatsapp(self) -> int:
        metrics = self.contact_metrics
        if "total_whatsapp" in metrics:
            return metrics["total_whatsapp"]
        if self.items:
            return sum(1 for it in self.items if bool(it.whatsapp))
        return 0

    @property
    def total_missing_phone(self) -> int:
        metrics = self.contact_metrics
        if "total_missing_phone" in metrics:
            return metrics["total_missing_phone"]
        if self.items:
            return sum(1 for it in self.items if not (it.mobile or it.phone or it.whatsapp))
        return 0

    @property
    def total_enriched(self) -> int:
        metrics = self.contact_metrics
        return metrics.get("total_enriched", 0)

    @property
    def total_enrichment_unavailable(self) -> int:
        metrics = self.contact_metrics
        return metrics.get("total_enrichment_unavailable", 0)


class DiscoveryJobItem(Base, TimestampMixin):
    __tablename__ = "discovery_job_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)
    raw_payload = Column(Text, nullable=True)
    business_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    phone = Column(String(100), nullable=True)
    mobile = Column(String(100), nullable=True)
    whatsapp = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    source_code = Column(String(50), nullable=True)
    is_eligible_for_crm = Column(Boolean, default=False, nullable=False)
    is_saved = Column(Boolean, default=False, nullable=False, index=True)
    is_already_saved = Column(Boolean, default=False, nullable=False, index=True)
    rejection_reason = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    job = relationship("DiscoveryJob", back_populates="items")
    branch = relationship("Branch")


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

