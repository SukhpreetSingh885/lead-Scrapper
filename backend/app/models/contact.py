from sqlalchemy import Column, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class BusinessContact(Base, TimestampMixin):
    __tablename__ = "business_contacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type = Column(String(20), nullable=False)  # mobile, landline, whatsapp, email
    original_value = Column(String(255), nullable=False)
    normalized_value = Column(String(255), nullable=False, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    source = Column(String(100), default="website_enrichment", nullable=False)
    source_url = Column(String(500), nullable=True)
    evidence = Column(String(500), nullable=True)

    branch = relationship("Branch", back_populates="contacts")

    __table_args__ = (
        Index("idx_contact_branch_normval", "branch_id", "contact_type", "normalized_value", unique=True),
        Index("idx_contact_type_normval", "contact_type", "normalized_value"),
    )

