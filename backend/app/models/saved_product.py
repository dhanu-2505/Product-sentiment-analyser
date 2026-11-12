from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship, synonym

from app.database.database import Base


class SavedProduct(Base):
    __tablename__ = "saved_products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    saved_at = Column(DateTime, default=datetime.utcnow)
    created_at = synonym("saved_at")

    user = relationship("User", back_populates="saved_products")
    product = relationship("Product", backref="saved_by_users")
