import re
from datetime import datetime
from typing import Any

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.models import Alert, AnalysisHistory, Product, ProductSource, Review, SavedProduct, SearchHistory, SentimentResult, SourceObservation
from app.services.analytics.sentiment_analytics import (
    compute_rating_distribution,
    compute_sentiment_trend,
    compute_summary,
    compute_word_frequency,
)
from app.services.scraper.scraper_manager import ScraperManager
from app.services.auth import get_optional_current_user
from app.services.source_evidence import reviews_for_source
from app.services.sentiment.vader_service import VaderSentimentService
from app.sources.catalog import SUPPORTED_SOURCES

router = APIRouter(tags=["products"])

scraper_manager = ScraperManager(timeout=settings.scraper_timeout, headless=settings.scraper_headless)
service = VaderSentimentService()
VALID_PLATFORMS = {"amazon", "flipkart"}
SOURCE_NAMES = {source.code: source.name for source in SUPPORTED_SOURCES}
SOURCE_CODES = set(SOURCE_NAMES)


def _normalize_platform(platform: str | None) -> str:
    normalized = (platform or "amazon").strip().lower()
    if normalized not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'flipkart'")
    return normalized


def _normalize_source(source: str | None) -> str:
    normalized = (source or "amazon").strip().lower()
    if normalized not in SOURCE_CODES:
        raise HTTPException(status_code=400, detail="Select a configured product source.")
    return normalized


def _normalize_product_identity(value: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def _find_source_product(db: Session, query: str, source_code: str) -> tuple[Product | None, ProductSource | None, bool]:
    linked_rows = (
        db.query(Product, ProductSource)
        .join(ProductSource, ProductSource.product_id == Product.id)
        .filter(func.lower(ProductSource.source_name) == source_code)
        .all()
    )
    candidates = {product.id: (product, source_record, False) for product, source_record in linked_rows}

    if source_code in VALID_PLATFORMS:
        legacy_products = db.query(Product).filter(
            Product.platform == source_code,
            or_(Product.name.ilike(f"%{query}%"), Product.brand.ilike(f"%{query}%")),
        ).all()
        for product in legacy_products:
            candidates.setdefault(product.id, (product, None, True))

    query_key = _normalize_product_identity(query)
    exact = [
        item for item in candidates.values()
        if _normalize_product_identity(item[0].name) == query_key
        or _normalize_product_identity(f"{item[0].brand or ''} {item[0].name}") == query_key
    ]
    if len(exact) == 1:
        product, source_record, is_legacy = exact[0]
        if source_record is None and is_legacy:
            source_record = ProductSource(
                product_id=product.id,
                source_name=source_code,
                product_url=None,
                data_type="seeded_demo" if product.is_demo else "stored",
            )
            db.add(source_record)
            db.flush()
        return product, source_record, is_legacy

    query_tokens = set(query_key.split())
    potential = [
        item for item in candidates.values()
        if query_tokens & set(_normalize_product_identity(f"{item[0].brand or ''} {item[0].name}").split())
    ]
    if exact or potential:
        raise HTTPException(
            status_code=409,
            detail=f"Potential match — identity not verified for {SOURCE_NAMES[source_code]}. Search using the full product name or model.",
        )

    return None, None, False


def _source_reviews(db: Session, product: Product, source_code: str, include_legacy_reviews: bool = False) -> list[Review]:
    if include_legacy_reviews:
        return reviews_for_source(db, product, source_code)
    return db.query(Review).filter(
        Review.product_id == product.id,
        func.lower(Review.source) == source_code,
    ).all()


def _parse_date(value: Any) -> datetime:
    if value is None:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return datetime.utcnow()
    return datetime.utcnow()


def _product_response(product: Product) -> dict:
    price_value = 0
    try:
        price_value = float((product.price or "0").replace("₹", "").replace(",", "").replace("$", ""))
    except Exception:
        price_value = 0

    reviews = product.reviews or []
    review_payload = [
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in reviews
    ]
    summary = compute_summary(review_payload)

    return {
        "id": product.id,
        "name": product.name,
        "platform": product.platform,
        "brand": product.brand,
        "category": product.category,
        "subcategory": product.subcategory,
        "source": product.source,
        "data_type": "seeded_demo" if product.is_demo else (product.source or "unverified"),
        "product_url": product.product_url,
        "image_url": product.image_url,
        "description": product.description,
        "features": (product.features or "").split(";") if product.features else [],
        "price": product.price,
        "price_value": price_value,
        "average_rating": round(float(product.average_rating or summary.get("average_rating", 0)), 2),
        "total_reviews": int(product.total_reviews or summary.get("total_reviews", 0)),
        "positive_percentage": summary.get("positive_percentage", 0),
        "neutral_percentage": summary.get("neutral_percentage", 0),
        "negative_percentage": summary.get("negative_percentage", 0),
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _build_review_payload(review: Review) -> dict:
    sentiment_label = "neutral"
    sentiment_score = 0.0
    compound_score = 0.0
    if review.sentiment:
        sentiment_label = review.sentiment.sentiment_label
        sentiment_score = review.sentiment.sentiment_score
        compound_score = review.sentiment.compound_score

    return {
        "id": review.id,
        "product_id": review.product_id,
        "reviewer_name": review.reviewer_name,
        "review_text": review.review_text,
        "rating": review.rating,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "compound_score": compound_score,
    }


def _save_analysis_history(db: Session, product_id: int) -> None:
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    review_payload = [
        {
            "sentiment": (review.sentiment.sentiment_label if review.sentiment else "neutral"),
            "rating": review.rating,
        }
        for review in reviews
    ]
    summary = compute_summary(review_payload)

    product = db.query(Product).filter(Product.id == product_id).first()
    previous = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.product_id == product_id)
        .order_by(AnalysisHistory.analyzed_at.desc(), AnalysisHistory.id.desc())
        .first()
    )
    if previous and abs(summary["positive_percentage"] - previous.positive_percentage) >= 15:
        watchers = db.query(SavedProduct).filter(SavedProduct.product_id == product_id).all()
        for watcher in watchers:
            existing_alert = db.query(Alert).filter(
                Alert.user_id == watcher.user_id,
                Alert.product_id == product_id,
                Alert.alert_type == "sentiment_change",
                Alert.is_read.is_(False),
            ).first()
            if existing_alert is None:
                db.add(Alert(
                    user_id=watcher.user_id,
                    product_id=product_id,
                    alert_type="sentiment_change",
                    message="Sentiment change detected.",
                ))
    if product is not None:
        product.average_rating = summary["average_rating"]
        product.total_reviews = summary["total_reviews"]

    history = AnalysisHistory(
        product_id=product_id,
        total_reviews=summary["total_reviews"],
        positive_count=summary["positive_count"],
        neutral_count=summary["neutral_count"],
        negative_count=summary["negative_count"],
        positive_percentage=summary["positive_percentage"],
        neutral_percentage=summary["neutral_percentage"],
        negative_percentage=summary["negative_percentage"],
        average_rating=summary["average_rating"],
        analyzed_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()


def _ensure_scraped_product(db: Session, product_name: str, platform: str, scrape_result: dict) -> Product:
    platform_name = _normalize_platform(platform)
    data_type = scrape_result.get("data_type", "unverified")
    product = db.query(Product).filter(Product.name == product_name, Product.platform == platform_name).first()
    if product is None:
        product = Product(
            name=product_name,
            platform=platform_name,
            source=platform_name,
            product_url=scrape_result.get("product_url"),
            image_url=scrape_result.get("image_url"),
            average_rating=float(scrape_result.get("rating") or 0),
            total_reviews=0,
            is_demo=data_type == "seeded_demo",
        )
        db.add(product)
        db.flush()
    else:
        product.product_url = scrape_result.get("product_url") or product.product_url
        product.image_url = scrape_result.get("image_url") or product.image_url

    source_record = db.query(ProductSource).filter_by(product_id=product.id, source_name=platform_name).first()
    if source_record is None:
        source_record = ProductSource(
            product_id=product.id,
            source_name=platform_name,
            product_url=scrape_result.get("product_url"),
            source_product_id=scrape_result.get("source_product_id"),
            data_type=data_type if data_type in {"live_scraped", "seeded_demo"} else "stored",
        )
        db.add(source_record)
        db.flush()
    else:
        source_record.product_url = scrape_result.get("product_url") or source_record.product_url
        source_record.data_type = data_type if data_type in {"live_scraped", "seeded_demo"} else "stored"
    if data_type == "live_scraped":
        source_record.last_scraped_at = datetime.utcnow()

    observation_values = {
        "price": scrape_result.get("price"),
        "currency": scrape_result.get("currency"),
        "rating": scrape_result.get("rating"),
        "review_count": scrape_result.get("review_count"),
        "availability": scrape_result.get("availability"),
    }
    if any(value is not None for value in observation_values.values()) and data_type in {"live_scraped", "seeded_demo"}:
        db.add(SourceObservation(product_source_id=source_record.id, data_type=data_type, **observation_values))

    for review_data in scrape_result.get("reviews", []):
        reviewer_name = (review_data.get("reviewer_name") or "Anonymous").strip() or "Anonymous"
        review_text = (review_data.get("review_text") or "").strip()
        if not review_text:
            continue

        existing_review = (
            db.query(Review)
            .filter(Review.product_id == product.id, Review.reviewer_name == reviewer_name, Review.review_text == review_text)
            .first()
        )
        if existing_review is not None:
            continue

        review = Review(
            product_id=product.id,
            reviewer_name=reviewer_name,
            review_text=review_text,
            rating=int(review_data.get("rating", 3) or 3),
            review_date=_parse_date(review_data.get("review_date")),
            source=platform_name,
            source_id=source_record.id,
            is_demo=data_type == "seeded_demo",
            data_type=data_type if data_type in {"live_scraped", "seeded_demo"} else "unverified",
            verified_purchase=bool(review_data.get("verified_purchase", False)),
        )
        db.add(review)
        db.flush()

        sentiment = service.analyze_text(review_text)
        sentiment_result = SentimentResult(
            review_id=review.id,
            sentiment_label=sentiment["sentiment_label"],
            sentiment_score=sentiment["sentiment_score"],
            compound_score=sentiment["compound_score"],
            positive_score=sentiment["positive_score"],
            neutral_score=sentiment["neutral_score"],
            negative_score=sentiment["negative_score"],
        )
        db.add(sentiment_result)

    db.flush()
    _save_analysis_history(db, product.id)
    db.refresh(product)
    return product


@router.get("/products")
def list_products(
    q: str = Query(default=""),
    category: str | None = None,
    brand: str | None = None,
    min_rating: float | None = None,
    source: str | None = None,
    sort: str = "rating",
    page: int = Query(default=1, ge=1),
    limit: int | None = Query(default=None, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.category.ilike(search_term),
                Product.subcategory.ilike(search_term),
            )
        )
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_rating is not None:
        query = query.filter(Product.average_rating >= min_rating)
    if source:
        source_code = _normalize_source(source)
        source_product_ids = db.query(ProductSource.product_id).filter(
            func.lower(ProductSource.source_name) == source_code,
        )
        if source_code in VALID_PLATFORMS:
            query = query.filter(or_(Product.id.in_(source_product_ids), Product.platform == source_code))
        else:
            query = query.filter(Product.id.in_(source_product_ids))

    if sort == "popular":
        query = query.order_by(Product.total_reviews.desc(), Product.average_rating.desc())
    elif sort == "price_asc":
        query = query.order_by(Product.price.desc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.asc())
    else:
        query = query.order_by(Product.average_rating.desc(), Product.total_reviews.desc())

    total = query.distinct().count()
    query = query.distinct()
    if limit is not None:
        query = query.offset((page - 1) * limit).limit(limit)
    products = query.all()
    return {
        "items": [_product_response(product) for product in products],
        "count": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@router.get("/products/search")
def search_products_get(
    query: str = "",
    platform: str = "amazon",
    source: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    return search_products(payload={"source": source or platform}, query=query, platform=platform, db=db, current_user=current_user)


@router.post("/products/analyze")
def analyze_product(
    payload: dict | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    body = payload or {}
    query_value = body.get("query") or body.get("product_name") or body.get("name")
    platform_value = body.get("source") or body.get("platform") or "amazon"
    return search_products(payload=body, query=query_value, platform=platform_value, db=db, current_user=current_user)


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_response(product)


@router.post("/products/search")
def search_products(
    payload: dict | None = None,
    query: str | None = None,
    platform: str = "amazon",
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    body = payload or {}
    query_value = query or body.get("query") or body.get("product_name")
    source_value = body.get("source") or body.get("platform") or platform
    if not query_value or not str(query_value).strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    source_code = _normalize_source(source_value)
    cleaned_query = str(query_value).strip()
    product, source_record, legacy_listing = _find_source_product(db, cleaned_query, source_code)
    created_from_source = False

    if product is None:
        if source_code not in VALID_PLATFORMS:
            raise HTTPException(
                status_code=404,
                detail=f"No matching observation found for this product on {SOURCE_NAMES[source_code]}. Try another product or select All Sources. Live retrieval unavailable for this source.",
            )
        scrape_result = scraper_manager.scrape(cleaned_query, source_code)
        if scrape_result.get("status") == "unavailable":
            raise HTTPException(
                status_code=503,
                detail=scrape_result.get("message", f"Live retrieval unavailable for {SOURCE_NAMES[source_code]}."),
            )
        product = _ensure_scraped_product(db, cleaned_query, source_code, scrape_result)
        source_record = db.query(ProductSource).filter_by(product_id=product.id, source_name=source_code).first()
        created_from_source = True

    if not created_from_source:
        _save_analysis_history(db, product.id)

    db.add(SearchHistory(
        user_id=current_user.id if current_user else None,
        query=cleaned_query,
        product_id=product.id,
        platform=source_code,
        searched_at=datetime.utcnow(),
    ))
    db.commit()

    source_reviews = _source_reviews(db, product, source_code, include_legacy_reviews=legacy_listing)
    summary = compute_summary([
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in source_reviews
    ])
    product_payload = _product_response(product)
    product_payload.update({
        "matched_source": source_code,
        "source_data_type": source_record.data_type if source_record else "unavailable",
        "match_quality": "exact_name",
    })
    return {"product": product_payload, "summary": summary, "message": "Product analysis completed"}


@router.get("/products/{product_id}/sentiment")
def get_product_sentiment(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    data = [{"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating} for review in reviews]
    summary = compute_summary(data)
    return {
        "product_id": product_id,
        "positive_count": summary["positive_count"],
        "neutral_count": summary["neutral_count"],
        "negative_count": summary["negative_count"],
        "overall_score": round(summary["positive_percentage"] - summary["negative_percentage"], 2),
    }
