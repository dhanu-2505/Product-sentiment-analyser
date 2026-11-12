from collections import Counter, defaultdict
from datetime import datetime

from app.services.sentiment.text_cleaner import clean_text

STOPWORDS = {
    "the", "is", "a", "an", "and", "of", "to", "for", "in", "on", "it", "this", "that",
    "with", "as", "at", "be", "by", "from", "or", "but", "not", "was", "were", "are", "if",
    "very", "so", "their", "them", "they", "our", "we", "you", "your", "i", "me", "my",
    "has", "have", "had", "can", "could", "should", "would", "more", "most", "than", "into",
    "out", "about", "after", "before", "there", "here", "just", "also", "still", "because",
}


def _extract_sentiment(item):
    if hasattr(item, "sentiment_label"):
        return str(getattr(item, "sentiment_label", "neutral")).lower()
    if isinstance(item, dict):
        value = item.get("sentiment") or item.get("sentiment_label") or "neutral"
        return str(value).lower()
    return "neutral"


def _extract_rating(item):
    if hasattr(item, "rating"):
        return int(getattr(item, "rating", 0) or 0)
    if isinstance(item, dict):
        return int(item.get("rating", 0) or 0)
    return 0


def compute_summary(reviews):
    if not reviews:
        return {
            "total_reviews": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_percentage": 0,
            "neutral_percentage": 0,
            "negative_percentage": 0,
            "average_rating": 0,
        }

    total = len(reviews)
    positive = sum(1 for item in reviews if _extract_sentiment(item) == "positive")
    neutral = sum(1 for item in reviews if _extract_sentiment(item) == "neutral")
    negative = sum(1 for item in reviews if _extract_sentiment(item) == "negative")
    rating_values = [_extract_rating(item) for item in reviews]

    return {
        "total_reviews": total,
        "positive_count": positive,
        "neutral_count": neutral,
        "negative_count": negative,
        "positive_percentage": round((positive / total) * 100, 2) if total else 0,
        "neutral_percentage": round((neutral / total) * 100, 2) if total else 0,
        "negative_percentage": round((negative / total) * 100, 2) if total else 0,
        "average_rating": round(sum(rating_values) / total, 2) if total else 0,
    }


def compute_rating_distribution(reviews):
    distribution = {str(i): 0 for i in range(1, 6)}
    for item in reviews:
        rating = _extract_rating(item)
        if 1 <= rating <= 5:
            distribution[str(rating)] += 1
    return distribution


def compute_word_frequency(review_texts):
    counts = Counter()
    for text in review_texts:
        cleaned = clean_text(text or "")
        for word in cleaned.split():
            if len(word) <= 2 or word in STOPWORDS:
                continue
            counts[word] += 1

    return [{"word": word, "count": count} for word, count in counts.most_common(20)]


def compute_sentiment_trend(reviews):
    grouped = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
    for item in reviews:
        date_value = getattr(item, "review_date", None)
        if isinstance(item, dict):
            date_value = item.get("review_date")
        if date_value is None:
            date_key = datetime.utcnow().date().isoformat()
        elif isinstance(date_value, str):
            try:
                date_key = datetime.fromisoformat(date_value).date().isoformat()
            except ValueError:
                date_key = datetime.utcnow().date().isoformat()
        else:
            date_key = date_value.date().isoformat()

        sentiment = _extract_sentiment(item)
        grouped[date_key][sentiment] += 1

    return [
        {
            "date": date,
            "positive": values["positive"],
            "neutral": values["neutral"],
            "negative": values["negative"],
        }
        for date, values in sorted(grouped.items())
    ]
