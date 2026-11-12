from pydantic import BaseModel, Field


class SentimentResultCreate(BaseModel):
    review_id: int
    sentiment_label: str = Field(..., min_length=1, max_length=20)
    sentiment_score: float = 0.0
    compound_score: float = 0.0
    positive_score: float = 0.0
    neutral_score: float = 0.0
    negative_score: float = 0.0


class SentimentResultRead(BaseModel):
    id: int
    review_id: int
    sentiment_label: str
    sentiment_score: float
    compound_score: float
    positive_score: float
    neutral_score: float
    negative_score: float
