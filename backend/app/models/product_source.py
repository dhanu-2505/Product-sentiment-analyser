from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.database import Base


class ProductSource(Base):
    __tablename__ = "product_sources"
    __table_args__ = (UniqueConstraint("product_id", "source_name", name="uq_product_sources_product_source"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)
    product_url = Column(String(500), nullable=True)
    source_product_id = Column(String(255), nullable=True)
    last_scraped_at = Column(DateTime, nullable=True)
    data_type = Column(String(20), nullable=False, default="stored")

    product = relationship("Product", backref="sources")
    reviews = relationship("Review", back_populates="product_source")
    observations = relationship("SourceObservation", cascade="all, delete-orphan")
