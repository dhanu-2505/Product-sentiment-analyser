import json
import math
from typing import Any, Dict, List


def compute_product_intelligence(
    reviews: List[Any],
    average_rating: float = 0.0,
    total_reviews: int = 0,
    positive_percentage: float = 0.0,
    neutral_percentage: float = 0.0,
    negative_percentage: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes a transparent, explainable Product Intelligence Score (0 to 100)
    derived mathematically from:
    1. Rating score (25%)
    2. Sentiment strength & confidence (30%)
    3. Aspect-level satisfaction (20%)
    4. Review volume reliability (15%)
    5. Review consistency & verified purchaser quality (10%)
    """
    if not reviews:
        return {
            "overall_score": None,
            "intelligence_score": None,
            "grade": "N/A",
            "recommendation": "Insufficient review data",
            "breakdown": {
                key: {"score": None, "weight": weight, "title": title, "detail": "No reviews available."}
                for key, weight, title in [
                    ("customer_sentiment", "30%", "Customer Sentiment"),
                    ("rating_quality", "25%", "Rating Quality"),
                    ("feature_satisfaction", "15%", "Feature Satisfaction"),
                    ("review_consistency", "10%", "Review Consistency"),
                    ("value_perception", "10%", "Value Perception"),
                    ("review_volume", "10%", "Review Volume"),
                ]
            },
            "aspect_breakdown": {},
            "key_strengths": [],
            "key_weaknesses": [],
        }

    # 1. Rating Factor (25%)
    actual_avg_rating = average_rating
    if reviews and not actual_avg_rating:
        ratings = [r.rating for r in reviews if getattr(r, "rating", None) is not None]
        if ratings:
            actual_avg_rating = sum(ratings) / len(ratings)

    rating_factor = min(100.0, max(0.0, (actual_avg_rating / 5.0) * 100.0))

    # 2. Sentiment Factor (30%)
    pos_pct = positive_percentage
    neg_pct = negative_percentage
    neu_pct = neutral_percentage
    if reviews and (pos_pct == 0 and neg_pct == 0 and neu_pct == 0):
        pos_count = sum(1 for r in reviews if getattr(r, "sentiment", None) and r.sentiment.sentiment_label == "positive")
        neg_count = sum(1 for r in reviews if getattr(r, "sentiment", None) and r.sentiment.sentiment_label == "negative")
        total = max(1, len(reviews))
        pos_pct = (pos_count / total) * 100.0
        neg_pct = (neg_count / total) * 100.0
        neu_pct = 100.0 - pos_pct - neg_pct

    sentiment_factor = max(0.0, min(100.0, pos_pct + (neu_pct * 0.5)))

    # 3. Aspect Factor (20%)
    aspect_counts: Dict[str, Dict[str, int]] = {}
    total_aspect_pos = 0
    total_aspect_neg = 0
    feature_counts = {"positive": 0, "neutral": 0, "negative": 0}
    value_counts = {"positive": 0, "neutral": 0, "negative": 0}

    for r in reviews:
        aspects_data = {}
        if getattr(r, "sentiment", None) and getattr(r.sentiment, "aspects_json", None):
            try:
                aspects_data = json.loads(r.sentiment.aspects_json or "{}")
            except Exception:
                aspects_data = {}

        for aspect_name, details in aspects_data.items():
            if aspect_name not in aspect_counts:
                aspect_counts[aspect_name] = {"positive": 0, "neutral": 0, "negative": 0}
            sent = details.get("sentiment", "neutral")
            if sent in aspect_counts[aspect_name]:
                aspect_counts[aspect_name][sent] += 1
                target_counts = value_counts if aspect_name.lower() == "price" else feature_counts
                target_counts[sent] += 1
            if sent == "positive":
                total_aspect_pos += 1
            elif sent == "negative":
                total_aspect_neg += 1

    feature_mentions = sum(feature_counts.values())
    feature_factor = (
        (feature_counts["positive"] + feature_counts["neutral"] * 0.5) / feature_mentions * 100.0
        if feature_mentions
        else None
    )
    value_mentions = sum(value_counts.values())
    value_factor = (
        (value_counts["positive"] + value_counts["neutral"] * 0.5) / value_mentions * 100.0
        if value_mentions
        else None
    )

    # 4. Volume Reliability Factor (15%)
    # Logarithmic scaling: 1 review ~ 15, 10 reviews ~ 45, 50 reviews ~ 76, 100+ reviews ~ 90-100
    review_count = total_reviews or len(reviews)
    volume_factor = min(100.0, max(20.0, math.log10(max(1, review_count) + 1) * 48.0))

    # 5. Consistency & Quality Factor (10%)
    if reviews:
        ratings = [r.rating for r in reviews if getattr(r, "rating", None) is not None]
        if len(ratings) > 1:
            mean = sum(ratings) / len(ratings)
            variance = sum((x - mean) ** 2 for x in ratings) / len(ratings)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.5

        verified_ratio = sum(1 for r in reviews if getattr(r, "verified_purchase", True)) / max(1, len(reviews))
        quality_avg = sum(getattr(r.sentiment, "quality_score", 0.8) for r in reviews if getattr(r, "sentiment", None)) / max(1, len(reviews))

        consistency_factor = max(10.0, min(100.0, (100.0 - (std_dev * 18.0)) * 0.5 + (verified_ratio * 25.0) + (quality_avg * 25.0)))
    else:
        consistency_factor = 75.0

    # Weighted score uses only observed ratings, review text, aspect mentions, and review quality.
    observed_components = [
        (sentiment_factor, 0.30),
        (rating_factor, 0.25),
        (feature_factor, 0.15),
        (consistency_factor, 0.10),
        (value_factor, 0.10),
        (volume_factor, 0.10),
    ]
    observed_weight = sum(weight for score, weight in observed_components if score is not None)
    total_score = sum(score * weight for score, weight in observed_components if score is not None) / observed_weight
    total_score = round(min(100.0, max(0.0, total_score)), 1)

    # Classification Grade
    if total_score >= 88:
        grade = "A+"
        recommendation = "Outstanding Market Leader"
    elif total_score >= 80:
        grade = "A"
        recommendation = "Strong Consumer Favorite"
    elif total_score >= 70:
        grade = "B"
        recommendation = "Good Competitive Option"
    elif total_score >= 60:
        grade = "C"
        recommendation = "Mixed Feedback / Niche Appeal"
    else:
        grade = "D"
        recommendation = "Critical Consumer Concerns"

    # Identify Key Strengths and Weaknesses from aspects
    key_strengths = []
    key_weaknesses = []
    for aspect_name, counts in aspect_counts.items():
        pos = counts.get("positive", 0)
        neg = counts.get("negative", 0)
        if pos > neg and pos >= 1:
            key_strengths.append({"aspect": aspect_name, "score": round((pos / (pos + neg)) * 100, 1), "positive_mentions": pos})
        elif neg > pos and neg >= 1:
            key_weaknesses.append({"aspect": aspect_name, "score": round((neg / (pos + neg)) * 100, 1), "negative_mentions": neg})

    key_strengths.sort(key=lambda x: x["positive_mentions"], reverse=True)
    key_weaknesses.sort(key=lambda x: x["negative_mentions"], reverse=True)

    rating_detail = {
        "score": round(rating_factor, 1),
        "weight": "25%",
        "title": "Rating Quality",
        "detail": f"Calculated from {round(actual_avg_rating, 2)}/5.0 average customer rating.",
    }
    sentiment_detail = {
        "score": round(sentiment_factor, 1),
        "weight": "30%",
        "title": "Customer Sentiment",
        "detail": f"{round(pos_pct, 1)}% positive, {round(neu_pct, 1)}% neutral, and {round(neg_pct, 1)}% negative reviews.",
    }
    feature_detail = {
        "score": round(feature_factor, 1) if feature_factor is not None else None,
        "weight": "15%",
        "title": "Feature Satisfaction",
        "detail": (
            f"{feature_counts['positive']} positive, {feature_counts['neutral']} neutral, and {feature_counts['negative']} negative feature mentions."
            if feature_factor is not None else "Insufficient feature-aspect mentions; excluded from the score."
        ),
    }
    consistency_detail = {
        "score": round(consistency_factor, 1),
        "weight": "10%",
        "title": "Review Consistency",
        "detail": "Rating variation, verified-purchase share, and text quality are combined.",
    }
    value_detail = {
        "score": round(value_factor, 1) if value_factor is not None else None,
        "weight": "10%",
        "title": "Value Perception",
        "detail": (
            f"Based on {value_mentions} detected price/value aspect mentions."
            if value_factor is not None else "Insufficient price/value mentions; excluded from the score."
        ),
    }
    volume_detail = {
        "score": round(volume_factor, 1),
        "weight": "10%",
        "title": "Review Volume",
        "detail": f"Logarithmic evidence-volume score from {review_count} reviews.",
    }

    return {
        "overall_score": total_score,
        "intelligence_score": total_score,
        "grade": grade,
        "recommendation": recommendation,
        "breakdown": {
            "customer_sentiment": sentiment_detail,
            "rating_quality": rating_detail,
            "feature_satisfaction": feature_detail,
            "review_consistency": consistency_detail,
            "value_perception": value_detail,
            "review_volume": volume_detail,
            "sentiment_factor": sentiment_detail,
            "rating_factor": rating_detail,
            "aspect_factor": feature_detail,
            "consistency_factor": consistency_detail,
            "volume_factor": volume_detail,
        },
        "aspect_breakdown": aspect_counts,
        "key_strengths": [s["aspect"] for s in key_strengths[:4]],
        "key_weaknesses": [w["aspect"] for w in key_weaknesses[:4]],
    }
