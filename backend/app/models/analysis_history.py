from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import synonym

from app.database.database import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    total_reviews = Column(Integer, nullable=False, default=0)
    positive_count = Column(Integer, nullable=False, default=0)
    neutral_count = Column(Integer, nullable=False, default=0)
    negative_count = Column(Integer, nullable=False, default=0)
    positive_percentage = Column(Float, nullable=False, default=0.0)
    neutral_percentage = Column(Float, nullable=False, default=0.0)
    negative_percentage = Column(Float, nullable=False, default=0.0)
    average_rating = Column(Float, nullable=False, default=0.0)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    recorded_at = synonym("analyzed_at")
