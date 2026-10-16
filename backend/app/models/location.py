from sqlalchemy import Column, Integer, String, Float, Boolean, Index
from app.models.base import Base


class IndiaLocation(Base):
    __tablename__ = "india_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    locality = Column(String(255), nullable=True, index=True)
    pincode = Column(String(10), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_india_loc_city_state", "city", "state"),
        Index("idx_india_loc_pincode", "pincode"),
    )

