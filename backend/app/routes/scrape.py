from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.models import Product, Review
from app.routes.products import _ensure_scraped_product
from app.services.analytics.sentiment_analytics import compute_summary
from app.services.scraper.scraper_manager import ScraperManager

router = APIRouter(tags=["scrape"])
scraper_manager = ScraperManager(timeout=settings.scraper_timeout, headless=settings.scraper_headless)
@router.post("/scrape")
def scrape_product(payload: dict | None = None, product_name: str | None = None, platform: str = "amazon", db: Session = Depends(get_db)):
    body = payload or {}
    name_value = product_name or body.get("product_name") or body.get("query")
    platform_value = (platform if platform != "amazon" or not body.get("platform") else body.get("platform") or platform).strip().lower()
    if not name_value or not str(name_value).strip():
        raise HTTPException(status_code=400, detail="Product name is required")
    if platform_value not in {"amazon", "flipkart"}:
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'flipkart'")

    name = str(name_value).strip()
    result = scraper_manager.scrape(name, platform_value)
    product = db.query(Product).filter(Product.name == name, Product.platform == platform_value).first()
    if result.get("status") == "unavailable":
        if product is None:
            return {"status": "unavailable", "message": result.get("message"), "data_type": "unavailable"}
        data_type = "stored"
    else:
        product = _ensure_scraped_product(db, name, platform_value, result)
        data_type = result.get("data_type", "unverified")

    return {
        "status": data_type,
        "message": result.get("message") or ("Using previously stored product data." if data_type == "stored" else "Product data saved."),
        "data_type": data_type,
        "product": {
            "id": product.id,
            "name": product.name,
            "platform": product.platform,
            "product_url": product.product_url,
            "image_url": product.image_url,
            "average_rating": round(float(product.average_rating or 0), 2),
            "total_reviews": product.total_reviews,
        },
        "reviews_count": product.total_reviews,
    }


@router.post("/scrape/analyze")
def scrape_and_analyze(payload: dict | None = None, product_name: str | None = None, platform: str = "amazon", db: Session = Depends(get_db)):
    body = payload or {}
    name_value = product_name or body.get("product_name") or body.get("query")
    platform_value = (platform if platform != "amazon" or not body.get("platform") else body.get("platform") or platform).strip().lower()
    if not name_value or not str(name_value).strip():
        raise HTTPException(status_code=400, detail="Product name is required")
    if platform_value not in {"amazon", "flipkart"}:
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'flipkart'")

    name = str(name_value).strip()
    result = scraper_manager.scrape(name, platform_value)
    product = db.query(Product).filter(Product.name == name, Product.platform == platform_value).first()
    if result.get("status") == "unavailable":
        if product is None:
            return {"status": "unavailable", "message": result.get("message"), "data_type": "unavailable"}
        data_type = "stored"
    else:
        product = _ensure_scraped_product(db, name, platform_value, result)
        data_type = result.get("data_type", "unverified")

    summary = compute_summary([
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in product.reviews
    ])
    db.commit()
    return {
        "status": data_type,
        "data_type": data_type,
        "message": result.get("message") or ("Using previously stored product data." if data_type == "stored" else "Product data saved."),
        "product_id": product.id,
        "product_name": product.name,
        "reviews_analyzed": summary["total_reviews"],
        "positive_count": summary["positive_count"],
        "neutral_count": summary["neutral_count"],
        "negative_count": summary["negative_count"],
    }
