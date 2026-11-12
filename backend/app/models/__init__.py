from app.models.alert import Alert
from app.models.analysis_history import AnalysisHistory
from app.models.product import Product
from app.models.product_source import ProductSource
from app.models.report import Report
from app.models.review import Review
from app.models.review_aspect import ReviewAspect
from app.models.saved_product import SavedProduct
from app.models.search_history import SearchHistory
from app.models.sentiment_result import SentimentResult
from app.models.source_observation import SourceObservation
from app.models.user import User

ReviewSentiment = SentimentResult
SentimentHistory = AnalysisHistory
Watchlist = SavedProduct

__all__ = [
    "Alert",
    "AnalysisHistory",
    "Product",
    "ProductSource",
    "Report",
    "Review",
    "ReviewSentiment",
    "ReviewAspect",
    "SavedProduct",
    "SearchHistory",
    "SentimentHistory",
    "SentimentResult",
    "SourceObservation",
    "User",
    "Watchlist",
]
