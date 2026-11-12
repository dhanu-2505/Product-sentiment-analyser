from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.models import Product, Review, ReviewAspect, SentimentResult
from app.services.analytics.review_quality import analyze_review_patterns
from app.services.source_evidence import reviews_for_source
from app.sources.catalog import SUPPORTED_SOURCES

router = APIRouter(tags=["reviews"])


def _review_response(review: Review) -> dict:
    sentiment_label = "neutral"
    sentiment_score = 0.0
    compound_score = 0.0
    polarity = 0.0
    subjectivity = 0.0
    confidence = 0.0
    quality_score = None

    if review.sentiment:
        sentiment_label = review.sentiment.sentiment_label
        sentiment_score = review.sentiment.sentiment_score
        compound_score = review.sentiment.compound_score
        polarity = review.sentiment.polarity_score
        subjectivity = review.sentiment.subjectivity_score
        confidence = review.sentiment.confidence_score
        quality_score = review.sentiment.quality_score

    aspects_list = []
    if hasattr(review, "aspects") and review.aspects:
        aspects_list = [
            {"aspect": a.aspect, "sentiment": a.sentiment, "score": a.score}
            for a in review.aspects
        ]

    return {
        "id": review.id,
        "product_id": review.product_id,
        "reviewer_name": review.reviewer_name,
        "rating": review.rating,
        "review_text": review.review_text,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "source": review.source,
        "is_demo": review.is_demo,
        "data_type": review.data_type,
        "verified_purchase": review.verified_purchase,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "compound_score": compound_score,
        "polarity": polarity,
        "subjectivity": subjectivity,
        "confidence": confidence,
        "quality_score": quality_score,
        "aspects": aspects_list,
    }


@router.get("/reviews/{review_id}")
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return _review_response(review)


@router.get("/products/{product_id}/reviews")
def get_reviews_for_product(
    product_id: int,
    search: str | None = Query(default=None),
    sentiment: str | None = Query(default=None),
    rating: int | None = Query(default=None, ge=1, le=5),
    aspect: str | None = Query(default=None),
    source: str | None = Query(default=None),
    data_type: str | None = Query(default=None),
    verified_purchase: bool | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    query = db.query(Review).filter(Review.product_id == product_id)

    if source:
        source_code = source.strip().lower()
        if source_code not in {item.code for item in SUPPORTED_SOURCES}:
            raise HTTPException(status_code=400, detail="Select a configured product source.")
        source_reviews = reviews_for_source(db, product, source_code)
        query = query.filter(Review.id.in_([review.id for review in source_reviews]))

    if search:
        query = query.filter(
            (Review.review_text.ilike(f"%{search}%"))
            | (Review.reviewer_name.ilike(f"%{search}%"))
        )
    if sentiment:
        sentiment_lower = sentiment.lower()
        query = query.join(Review.sentiment).filter(Review.sentiment.has(sentiment_label=sentiment_lower))
    if rating is not None:
        query = query.filter(Review.rating == rating)
    if aspect:
        review_ids_with_aspect = (
            db.query(ReviewAspect.review_id)
            .filter(ReviewAspect.aspect.ilike(f"%{aspect}%"))
            .subquery()
        )
        query = query.filter(Review.id.in_(review_ids_with_aspect))
    if data_type:
        if data_type not in {"live_scraped", "stored", "seeded_demo", "unverified"}:
            raise HTTPException(status_code=400, detail="Unsupported review data provenance.")
        query = query.filter(Review.data_type == data_type)
    if verified_purchase is not None:
        query = query.filter(Review.verified_purchase.is_(verified_purchase))
    if start_date:
        query = query.filter(Review.review_date >= start_date)
    if end_date:
        query = query.filter(Review.review_date <= end_date)

    # Sorting
    if sort == "oldest":
        query = query.order_by(Review.review_date.asc(), Review.id.asc())
    elif sort == "highest":
        query = query.order_by(Review.rating.desc(), Review.id.desc())
    elif sort == "lowest":
        query = query.order_by(Review.rating.asc(), Review.id.asc())
    elif sort == "confidence":
        query = query.outerjoin(Review.sentiment).order_by(SentimentResult.confidence_score.desc(), Review.id.desc())
    else:  # newest
        query = query.order_by(Review.review_date.desc(), Review.id.desc())

    total = query.count()
    offset = (page - 1) * limit
    reviews = query.offset(offset).limit(limit).all()

    return {
        "product_id": product_id,
        "items": [_review_response(review) for review in reviews],
        "count": len(reviews),
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@router.get("/products/{product_id}/review-quality")
def get_review_quality(product_id: int, source: str | None = Query(default=None), db: Session = Depends(get_db)):
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
    return {"product_id": product_id, **analyze_review_patterns(reviews)}
