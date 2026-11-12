from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, synonym

from app.database.database import Base


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True, index=True)
    sentiment_label = Column(String(20), nullable=False)
    sentiment = synonym("sentiment_label")
    sentiment_score = Column(Float, nullable=False, default=0.0)
    compound_score = Column(Float, nullable=False, default=0.0)
    positive_score = Column(Float, nullable=False, default=0.0)
    neutral_score = Column(Float, nullable=False, default=0.0)
    negative_score = Column(Float, nullable=False, default=0.0)
    polarity_score = Column(Float, nullable=False, default=0.0)
    polarity = synonym("polarity_score")
    subjectivity_score = Column(Float, nullable=False, default=0.0)
    subjectivity = synonym("subjectivity_score")
    confidence_score = Column(Float, nullable=False, default=0.0)
    confidence = synonym("confidence_score")
    aspects_json = Column(Text, nullable=True, default="{}")
    quality_score = Column(Float, nullable=False, default=1.0)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="sentiment")
