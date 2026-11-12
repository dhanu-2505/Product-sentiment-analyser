from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("product_sources.id"), nullable=True, index=True)
    reviewer_name = Column(String(150), nullable=True)
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    review_date = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True, default="demo")
    is_demo = Column(Boolean, default=True, nullable=False)
    data_type = Column(String(20), nullable=False, default="seeded_demo", index=True)
    verified_purchase = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="reviews")
    product_source = relationship("ProductSource", back_populates="reviews")
    sentiment = relationship("SentimentResult", back_populates="review", uselist=False)
