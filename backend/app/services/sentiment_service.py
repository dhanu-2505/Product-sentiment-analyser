from textblob import TextBlob

from app.services.sentiment.aspect_service import AspectSentimentService
from app.services.sentiment.vader_service import VaderSentimentService


class SentimentAnalyzerService:
    """Combine VADER, TextBlob, and Aspect Analysis into a rich sentiment payload."""

    def __init__(self) -> None:
        self.vader = VaderSentimentService()
        self.aspect_service = AspectSentimentService()

    def analyze(self, text: str, rating: int = 4, verified_purchase: bool = True) -> dict:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text must not be empty")

        vader_result = self.vader.analyze_text(text)
        blob = TextBlob(text)

        polarity = round(blob.sentiment.polarity, 4)
        subjectivity = round(blob.sentiment.subjectivity, 4)
        compound = vader_result["compound_score"]

        if compound >= 0.05 or polarity > 0.2:
            label = "positive"
        elif compound <= -0.05 or polarity < -0.2:
            label = "negative"
        else:
            label = "neutral"

        confidence = round(min(0.99, max(0.2, abs(compound) * 0.9 + abs(polarity) * 0.6 + 0.2)), 4)
        aspects = self.aspect_service.extract_aspects(text)
        quality = self.aspect_service.compute_review_quality(text, rating, label, verified_purchase)

        return {
            "sentiment_label": label,
            "polarity_score": polarity,
            "subjectivity_score": subjectivity,
            "confidence_score": confidence,
            "compound_score": compound,
            "positive_score": vader_result["positive_score"],
            "neutral_score": vader_result["neutral_score"],
            "negative_score": vader_result["negative_score"],
            "aspects": aspects,
            "quality_score": quality,
        }
