from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Product, ProductSource, SourceObservation, User
from app.services.auth import get_current_user
from app.services.analytics.observation_alerts import create_observation_change_alerts
from app.sources import SourceManager, SUPPORTED_SOURCES

router = APIRouter(tags=["sources"])
source_manager = SourceManager()


class StoredObservationRequest(BaseModel):
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    availability: bool | None = None


@router.get("/sources")
def list_sources():
    return {"items": source_manager.list_sources(), "count": len(source_manager.sources)}


@router.get("/products/{product_id}/sources")
def get_product_sources(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "product_id": product_id,
        "product_name": product.name,
        "items": source_manager.product_sources(db, product_id),
        "count": len(source_manager.sources),
    }


@router.post("/products/{product_id}/sources/{source_code}/observations", status_code=201)
def record_source_observation(
    product_id: int,
    source_code: str,
    payload: StoredObservationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    definition = next((item for item in SUPPORTED_SOURCES if item.code == source_code.lower()), None)
    if definition is None:
        raise HTTPException(status_code=404, detail="Unsupported source.")
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    if all(value is None for value in payload.model_dump().values()):
        raise HTTPException(status_code=400, detail="At least one observed field is required.")

    source = db.query(ProductSource).filter_by(product_id=product_id, source_name=definition.code).first()
    if source is None:
        source = ProductSource(product_id=product_id, source_name=definition.code, data_type="stored")
        db.add(source)
        db.flush()

    previous = (
        db.query(SourceObservation)
        .filter(
            SourceObservation.product_source_id == source.id,
            SourceObservation.data_type.in_(["stored", "live_scraped"]),
        )
        .order_by(SourceObservation.observed_at.desc(), SourceObservation.id.desc())
        .first()
    )
    observation = SourceObservation(
        product_source_id=source.id,
        data_type="stored",
        **payload.model_dump(),
    )
    db.add(observation)
    db.flush()
    alerts = create_observation_change_alerts(db, source, previous, observation)
    db.commit()

    return {
        "product_id": product_id,
        "source": definition.code,
        "status": "stored",
        "message": "Observation stored as supplied; no retailer was contacted.",
        "observation_id": observation.id,
        "observed_at": observation.observed_at.isoformat() if observation.observed_at else None,
        "alerts_created": len(alerts),
    }
