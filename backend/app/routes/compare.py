import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Product, Review, ReviewAspect
from app.services.analytics.product_intelligence import compute_product_intelligence
from app.services.analytics.sentiment_analytics import compute_summary

router = APIRouter(tags=["compare"])


class CompareRequest(BaseModel):
    product_ids: list[int]


@router.post("/compare")
def compare_products(payload: CompareRequest, db: Session = Depends(get_db)):
    product_ids = list(dict.fromkeys(payload.product_ids))
    if len(product_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least two product ids to compare.")
    if len(product_ids) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 products can be compared at once.")

    items = []
    for product_id in product_ids:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} was not found.")

        reviews = db.query(Review).filter(Review.product_id == product_id).all()
        summary = compute_summary([
            {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
            for review in reviews
        ])

        # Intelligence score
        intelligence = compute_product_intelligence(
            reviews=reviews,
            average_rating=float(product.average_rating or 0),
            total_reviews=int(product.total_reviews or 0),
            positive_percentage=summary["positive_percentage"],
            neutral_percentage=summary["neutral_percentage"],
            negative_percentage=summary["negative_percentage"],
        )

        # Aspect summary
        aspect_rows = db.query(ReviewAspect).filter(
            ReviewAspect.review_id.in_([r.id for r in reviews])
        ).all() if reviews else []

        aspect_sentiment = {}
        for row in aspect_rows:
            if row.aspect not in aspect_sentiment:
                aspect_sentiment[row.aspect] = {"positive": 0, "neutral": 0, "negative": 0}
            aspect_sentiment[row.aspect][row.sentiment] += 1

        # Fallback to aspects_json
        if not aspect_sentiment:
            for review in reviews:
                if review.sentiment and review.sentiment.aspects_json:
                    try:
                        aspects = json.loads(review.sentiment.aspects_json or "{}")
                        for aspect_name, details in aspects.items():
                            if aspect_name not in aspect_sentiment:
                                aspect_sentiment[aspect_name] = {"positive": 0, "neutral": 0, "negative": 0}
                            sent = details.get("sentiment", "neutral")
                            if sent in aspect_sentiment[aspect_name]:
                                aspect_sentiment[aspect_name][sent] += 1
                    except Exception:
                        pass

        price_value = 0
        try:
            price_value = float((product.price or "0").replace("₹", "").replace(",", "").replace("$", ""))
        except Exception:
            price_value = 0
        review_data_types = {review.data_type for review in reviews}
        review_provenance = (
            next(iter(review_data_types)) if len(review_data_types) == 1
            else "mixed" if review_data_types
            else "unavailable"
        )

        items.append({
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "platform": product.platform,
            "image_url": product.image_url,
            "price": product.price,
            "price_value": price_value,
            "price_data_type": "seeded_demo" if product.is_demo and product.price else "stored" if product.price else "unavailable",
            "average_rating": summary["average_rating"],
            "total_reviews": summary["total_reviews"],
            "review_data_type": review_provenance,
            "positive_percentage": summary["positive_percentage"],
            "neutral_percentage": summary["neutral_percentage"],
            "negative_percentage": summary["negative_percentage"],
            "intelligence_score": intelligence["intelligence_score"],
            "grade": intelligence["grade"],
            "aspect_sentiment": aspect_sentiment,
        })

    return {"count": len(items), "items": items}


@router.get("/compare")
def compare_products_get(
    ids: str = Query(default="", description="Comma-separated product IDs"),
    db: Session = Depends(get_db),
):
    if not ids.strip():
        raise HTTPException(status_code=400, detail="Provide comma-separated product IDs.")
    try:
        product_ids = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format.")

    return compare_products(payload=CompareRequest(product_ids=product_ids), db=db)
