from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    product_id: int
    reviewer_name: Optional[str] = None
    review_text: str = Field(..., min_length=2)
    rating: int = Field(..., ge=1, le=5)
    review_date: Optional[datetime] = None


class ReviewRead(BaseModel):
    id: int
    product_id: int
    reviewer_name: Optional[str] = None
    review_text: str
    rating: int
    review_date: Optional[datetime] = None
