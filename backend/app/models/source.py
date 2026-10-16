from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class LeadSource(Base, TimestampMixin):
    __tablename__ = "lead_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)  # google_places, google_search, licensed_csv, licensed_api, demo_fixture
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    requires_api_key = Column(Boolean, default=False, nullable=False)

    permissions = relationship("SourcePermission", back_populates="source", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="source")


class SourcePermission(Base, TimestampMixin):
    __tablename__ = "source_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("lead_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    license_name = Column(String(255), nullable=False)
    permitted_storage = Column(Boolean, default=False, nullable=False)
    permitted_export = Column(Boolean, default=False, nullable=False)
    permitted_enrichment = Column(Boolean, default=False, nullable=False)
    license_terms_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    source = relationship("LeadSource", back_populates="permissions")

