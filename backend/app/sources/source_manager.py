from sqlalchemy.orm import Session

from app.models import ProductSource, SourceObservation
from app.sources.base_source import UnavailableSource
from app.sources.catalog import SUPPORTED_SOURCES


class SourceManager:
    def __init__(self) -> None:
        self.sources = {source.code: UnavailableSource(source) for source in SUPPORTED_SOURCES}

    def list_sources(self) -> list[dict]:
        return [
            {
                "code": source.code,
                "name": source.name,
                "base_url": source.base_url,
                "status": "unavailable",
                "checked": False,
                "live_connector_configured": source.live_connector_configured,
                "message": (
                    "A live connector can be attempted; each result still requires verified source evidence."
                    if source.live_connector_configured
                    else "Live retrieval unavailable for this source."
                ),
            }
            for source in SUPPORTED_SOURCES
        ]

    def product_sources(self, db: Session, product_id: int) -> list[dict]:
        stored_sources = {
            source.source_name.strip().lower(): source
            for source in db.query(ProductSource).filter(ProductSource.product_id == product_id).all()
        }
        results = []
        for definition in SUPPORTED_SOURCES:
            stored = stored_sources.get(definition.code)
            if stored is None:
                results.append(
                    {
                        "source": definition.code,
                        "source_name": definition.name,
                        "status": "unavailable",
                        "checked": False,
                        "message": "Live data unavailable for this source.",
                        "price": None,
                        "rating": None,
                        "review_count": None,
                        "availability": None,
                        "last_checked_at": None,
                    }
                )
                continue

            observations = (
                db.query(SourceObservation)
                .filter(SourceObservation.product_source_id == stored.id)
                .order_by(SourceObservation.observed_at.desc(), SourceObservation.id.desc())
                .all()
            )
            observation = observations[0] if observations else None
            stored_type = observation.data_type if observation else (stored.data_type or "stored")
            provenance = "live" if stored_type == "live_scraped" else stored_type
            results.append(
                {
                    "source": definition.code,
                    "source_name": definition.name,
                    "status": provenance,
                    "checked": stored.last_scraped_at is not None,
                    "message": None,
                    "product_url": stored.product_url,
                    "price": float(observation.price) if observation and observation.price is not None else None,
                    "currency": observation.currency if observation else None,
                    "rating": observation.rating if observation else None,
                    "review_count": observation.review_count if observation else None,
                    "availability": observation.availability if observation else None,
                    "last_checked_at": stored.last_scraped_at.isoformat() if stored.last_scraped_at else None,
                    "observed_at": observation.observed_at.isoformat() if observation and observation.observed_at else None,
                    "price_history": [
                        {
                            "price": float(item.price) if item.price is not None else None,
                            "currency": item.currency,
                            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
                            "data_type": item.data_type,
                        }
                        for item in reversed(observations)
                        if item.price is not None
                    ],
                }
            )
        return results
