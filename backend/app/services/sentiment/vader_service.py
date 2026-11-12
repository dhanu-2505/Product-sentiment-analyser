from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class VaderSentimentService:
    def __init__(self, positive_threshold: float = 0.05, negative_threshold: float = -0.05):
        self.analyzer = SentimentIntensityAnalyzer()
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold

    def analyze_text(self, text: str):
        if not text or not str(text).strip():
            raise ValueError("Text must not be empty")

        scores = self.analyzer.polarity_scores(text)
        compound = scores.get("compound", 0.0)

        if compound >= self.positive_threshold:
            label = "positive"
        elif compound <= self.negative_threshold:
            label = "negative"
        else:
            label = "neutral"

        return {
            "sentiment_label": label,
            "sentiment_score": max(0.0, scores.get("pos", 0.0)),
            "compound_score": compound,
            "positive_score": scores.get("pos", 0.0),
            "neutral_score": scores.get("neu", 0.0),
            "negative_score": scores.get("neg", 0.0),
        }
