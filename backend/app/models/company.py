from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    website_domain = Column(String(255), nullable=True, index=True)
    primary_category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    organization = relationship("Organization", back_populates="companies")
    branches = relationship("Branch", back_populates="company", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_company_org_normname", "organization_id", "normalized_name"),
    )

