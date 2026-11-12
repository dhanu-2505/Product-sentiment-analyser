from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Product, Review


def reviews_for_source(db: Session, product: Product, source_code: str) -> list[Review]:
    source_reviews = db.query(Review).filter(
        Review.product_id == product.id,
        func.lower(Review.source) == source_code,
    ).all()
    if source_reviews or product.platform != source_code:
        return source_reviews

    return db.query(Review).filter(
        Review.product_id == product.id,
        Review.source_id.is_(None),
        Review.data_type.in_(("seeded_demo", "stored", "live_scraped")),
    ).all()