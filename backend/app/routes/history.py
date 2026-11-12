from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Product, Review, SearchHistory, User
from app.services.auth import get_current_user
from app.services.analytics.sentiment_analytics import compute_summary

router = APIRouter(tags=["history"])


def _history_response(history: SearchHistory, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == history.product_id).first() if history.product_id else None
    reviews = db.query(Review).filter(Review.product_id == history.product_id).all() if history.product_id else []
    summary = compute_summary([
        {"sentiment": review.sentiment.sentiment_label if review.sentiment else "neutral", "rating": review.rating}
        for review in reviews
    ])
    return {
        "id": history.id,
        "product_id": history.product_id,
        "query": history.query,
        "product_name": product.name if product else history.query,
        "platform": history.platform or (product.platform if product else "unknown"),
        "total_reviews": summary["total_reviews"],
        "positive_count": summary["positive_count"],
        "neutral_count": summary["neutral_count"],
        "negative_count": summary["negative_count"],
        "positive_percentage": summary["positive_percentage"],
        "neutral_percentage": summary["neutral_percentage"],
        "negative_percentage": summary["negative_percentage"],
        "average_rating": summary["average_rating"],
        "analyzed_at": history.searched_at.isoformat() if history.searched_at else None,
    }


@router.get("/history")
def list_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    histories = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(200)
        .all()
    )
    return {"items": [_history_response(history, db) for history in histories], "count": len(histories)}


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(SearchHistory).filter(SearchHistory.user_id == current_user.id)
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": True, "count": count}


@router.get("/history/{history_id}")
def get_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = db.query(SearchHistory).filter(
        SearchHistory.id == history_id,
        SearchHistory.user_id == current_user.id,
    ).first()
    if history is None:
        raise HTTPException(status_code=404, detail="History item not found")
    return _history_response(history, db)
