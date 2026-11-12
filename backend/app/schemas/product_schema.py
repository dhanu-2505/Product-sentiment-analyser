from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    platform: str = Field(..., min_length=2, max_length=50)
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    average_rating: float = 0.0
    total_reviews: int = 0


class ProductRead(BaseModel):
    id: int
    name: str
    platform: str
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    average_rating: float
    total_reviews: int
