from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String

from app.database.database import Base


class SourceObservation(Base):
    __tablename__ = "source_observations"

    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(8), nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    availability = Column(Boolean, nullable=True)
    data_type = Column(String(20), nullable=False)
    observed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
