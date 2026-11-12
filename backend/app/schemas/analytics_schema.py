from typing import List

from pydantic import BaseModel


class SentimentSummary(BaseModel):
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    average_rating: float


class WordFrequency(BaseModel):
    word: str
    count: int


class DashboardStats(BaseModel):
    total_products: int
    total_reviews: int
    average_sentiment: float
    positive_share: float
    neutral_share: float
    negative_share: float
    weekly_trend: List[int]
