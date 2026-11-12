import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import AnalysisHistory, Product, Review, ReviewAspect, SearchHistory, SentimentResult
from app.services.analytics.product_intelligence import compute_product_intelligence
from app.services.source_evidence import reviews_for_source
from app.sources.catalog import SUPPORTED_SOURCES
from app.services.analytics.sentiment_analytics import (
    compute_rating_distribution,
    compute_sentiment_trend,
    compute_summary,
    compute_word_frequency,
)

router = APIRouter(tags=["analytics"])


@router.get("/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    reviews = db.query(Review).all()
    review_data_types = {}
    for review in reviews:
        data_type = review.data_type or "unverified"
        review_data_types[data_type] = review_data_types.get(data_type, 0) + 1
    review_payload = [
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in reviews
    ]
    summary = compute_summary(review_payload)

    avg_product_rating = round(sum((product.average_rating or 0) for product in products) / len(products), 2) if products else 0
    today = datetime.utcnow().date()
    analyzed_today = sum(
        1 for product in products if product.created_at and product.created_at.date() == today
    )
    recent_searches = db.query(SearchHistory).order_by(SearchHistory.searched_at.desc()).limit(6).all()

    # Top categories breakdown
    category_counts = {}
    for product in products:
        cat = product.category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:8]

    # Top keywords from all reviews
    top_keywords = compute_word_frequency([r.review_text for r in reviews])

    # Rating distribution across all reviews
    rating_dist = compute_rating_distribution(reviews)

    # Sentiment trend across all reviews
    sentiment_trend = compute_sentiment_trend(reviews)

    return {
        "total_products": len(products),
        "total_reviews": len(reviews),
        "review_data_types": review_data_types,
        "positive_reviews_percentage": summary["positive_percentage"],
        "neutral_reviews_percentage": summary["neutral_percentage"],
        "negative_reviews_percentage": summary["negative_percentage"],
        "average_product_rating": avg_product_rating,
        "products_analyzed_today": analyzed_today,
        "rating_distribution": rating_dist,
        "sentiment_trend": sentiment_trend,
        "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
        "top_keywords": top_keywords[:10],
        "recent_searches": [
            {"query": item.query, "platform": item.platform, "searched_at": item.searched_at.isoformat() if item.searched_at else None}
            for item in recent_searches
        ],
    }


@router.get("/products/search-suggestions")
def search_suggestions(query: str = Query(default="", min_length=1), db: Session = Depends(get_db)):
    if not query.strip():
        return {"items": []}

    filters = [
        Product.name.ilike(f"%{query.strip()}%"),
        Product.brand.ilike(f"%{query.strip()}%"),
        Product.category.ilike(f"%{query.strip()}%"),
        Product.subcategory.ilike(f"%{query.strip()}%"),
    ]
    items = db.query(Product).filter(or_(*filters)).order_by(Product.total_reviews.desc(), Product.average_rating.desc()).limit(10).all()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "brand": item.brand,
                "category": item.category,
                "platform": item.platform,
                "average_rating": float(item.average_rating or 0),
                "image_url": item.image_url,
            }
            for item in items
        ]
    }


@router.get("/products/{product_id}/analytics")
def get_analytics(product_id: int, source: str | None = Query(default=None), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    if source:
        source_code = source.strip().lower()
        if source_code not in {item.code for item in SUPPORTED_SOURCES}:
            raise HTTPException(status_code=400, detail="Select a configured product source.")
        reviews = reviews_for_source(db, product, source_code)
    else:
        reviews = db.query(Review).filter(Review.product_id == product_id).all()
    payload = [
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in reviews
    ]
    summary = compute_summary(payload)
    rating_distribution = compute_rating_distribution(reviews)
    sentiment_trend = compute_sentiment_trend(reviews)
    word_freq = compute_word_frequency([review.review_text for review in reviews])

    # Aspect sentiment from review_aspects table
    aspect_rows = db.query(ReviewAspect).filter(ReviewAspect.review_id.in_([r.id for r in reviews])).all() if reviews else []
    aspect_summary = {}
    for row in aspect_rows:
        if row.aspect not in aspect_summary:
            aspect_summary[row.aspect] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0, "avg_score": 0.0, "scores": []}
        aspect_summary[row.aspect][row.sentiment] += 1
        aspect_summary[row.aspect]["total"] += 1
        aspect_summary[row.aspect]["scores"].append(row.score)

    top_aspects = []
    for aspect_name, data in aspect_summary.items():
        scores = data.pop("scores", [])
        data["avg_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0
        top_aspects.append({"aspect": aspect_name, **data})
    top_aspects.sort(key=lambda x: x["total"], reverse=True)

    # Fallback to aspects_json if no review_aspects rows
    if not top_aspects:
        aspect_counts = {}
        for review in reviews:
            if review.sentiment and review.sentiment.aspects_json:
                try:
                    aspects = json.loads(review.sentiment.aspects_json or "{}")
                    for aspect_name, details in aspects.items():
                        if aspect_name not in aspect_counts:
                            aspect_counts[aspect_name] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
                        sent = details.get("sentiment", "neutral")
                        if sent in aspect_counts[aspect_name]:
                            aspect_counts[aspect_name][sent] += 1
                        aspect_counts[aspect_name]["total"] += 1
                except Exception:
                    pass
        for aspect_name, data in aspect_counts.items():
            top_aspects.append({"aspect": aspect_name, "avg_score": 0.0, **data})
        top_aspects.sort(key=lambda x: x["total"], reverse=True)

    # Top positive/negative keywords
    positive_texts = [r.review_text for r in reviews if r.sentiment and r.sentiment.sentiment_label == "positive"]
    negative_texts = [r.review_text for r in reviews if r.sentiment and r.sentiment.sentiment_label == "negative"]
    top_positive_keywords = compute_word_frequency(positive_texts)[:10]
    top_negative_keywords = compute_word_frequency(negative_texts)[:10]

    # Customer praises and complaints (short excerpts from highly rated positive/negative reviews)
    praises = []
    complaints = []
    for review in sorted(reviews, key=lambda r: r.rating or 0, reverse=True):
        if review.sentiment and review.sentiment.sentiment_label == "positive" and len(praises) < 5:
            praises.append({"text": review.review_text[:200], "rating": review.rating, "reviewer": review.reviewer_name})
        elif review.sentiment and review.sentiment.sentiment_label == "negative" and len(complaints) < 5:
            complaints.append({"text": review.review_text[:200], "rating": review.rating, "reviewer": review.reviewer_name})
    # Reverse complaints so worst appear first
    complaints.sort(key=lambda x: x["rating"])

    # Product Intelligence Score
    intelligence = compute_product_intelligence(
        reviews=reviews,
        average_rating=summary["average_rating"],
        total_reviews=summary["total_reviews"],
        positive_percentage=summary["positive_percentage"],
        neutral_percentage=summary["neutral_percentage"],
        negative_percentage=summary["negative_percentage"],
    )

    # Sentiment history from analysis_history
    history_rows = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.product_id == product_id)
        .order_by(AnalysisHistory.analyzed_at.asc())
        .all()
    ) if not source else []
    sentiment_history = [
        {
            "date": h.analyzed_at.isoformat() if h.analyzed_at else None,
            "positive_percentage": h.positive_percentage,
            "neutral_percentage": h.neutral_percentage,
            "negative_percentage": h.negative_percentage,
            "average_rating": h.average_rating,
        }
        for h in history_rows
    ]

    return {
        "product_id": product_id,
        "product_name": product.name,
        "brand": product.brand,
        "category": product.category,
        "total_reviews": summary["total_reviews"],
        "average_rating": summary["average_rating"],
        "positive_count": summary["positive_count"],
        "neutral_count": summary["neutral_count"],
        "negative_count": summary["negative_count"],
        "positive_percentage": summary["positive_percentage"],
        "neutral_percentage": summary["neutral_percentage"],
        "negative_percentage": summary["negative_percentage"],
        "rating_distribution": rating_distribution,
        "sentiment_distribution": {
            "positive": summary["positive_count"],
            "neutral": summary["neutral_count"],
            "negative": summary["negative_count"],
        },
        "sentiment_trend": sentiment_trend,
        "sentiment_history": sentiment_history,
        "word_frequency": word_freq,
        "top_positive_keywords": top_positive_keywords,
        "top_negative_keywords": top_negative_keywords,
        "top_aspects": top_aspects,
        "customer_praises": praises,
        "customer_complaints": complaints,
        "product_intelligence": intelligence,
    }


@router.get("/products/{product_id}/word-frequency")
def get_word_frequency(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    return {"product_id": product_id, "words": compute_word_frequency([review.review_text for review in reviews])}
