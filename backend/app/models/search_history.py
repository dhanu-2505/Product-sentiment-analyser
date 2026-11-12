from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    query = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    platform = Column(String(50), nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="search_history")
    product = relationship("Product", backref="search_references")
