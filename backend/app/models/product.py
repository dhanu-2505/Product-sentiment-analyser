from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import synonym

from app.database.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False, default="amazon")
    brand = Column(String(150), nullable=True)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    product_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    price = Column(String(50), nullable=True)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    review_count = synonym("total_reviews")
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
