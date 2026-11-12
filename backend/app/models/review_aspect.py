from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class ReviewAspect(Base):
    __tablename__ = "review_aspects"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    aspect = Column(String(100), nullable=False, index=True)
    sentiment = Column(String(20), nullable=False)
    score = Column(Float, nullable=False, default=0.0)

    review = relationship("Review", backref="aspects")
