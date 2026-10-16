from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class Export(Base, TimestampMixin):
    __tablename__ = "exports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    file_format = Column(String(10), nullable=False)  # csv, xlsx
    filter_criteria = Column(Text, nullable=True)  # JSON filters
    file_path = Column(String(500), nullable=True)
    row_count = Column(Integer, default=0, nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, ready, failed
    download_token = Column(String(100), unique=True, index=True, nullable=False)
    error_message = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="exports")

