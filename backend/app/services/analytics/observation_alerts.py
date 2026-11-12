from app.models import Alert, ProductSource, SavedProduct, SourceObservation



def create_observation_change_alerts(db, source: ProductSource, previous: SourceObservation | None, current: SourceObservation) -> list[Alert]:
    if previous is None or previous.data_type not in {"stored", "live_scraped"}:
        return []
    if current.data_type not in {"stored", "live_scraped"}:
        return []

    changes = []
    if previous.price is not None and current.price is not None and previous.price != current.price:
        currency = current.currency or previous.currency or ""
        changes.append(("price_change", f"Price change recorded for {source.source_name}: {currency} {previous.price} to {currency} {current.price}."))
    if previous.rating is not None and current.rating is not None and previous.rating != current.rating:
        changes.append(("rating_change", f"Rating change recorded for {source.source_name}: {previous.rating} to {current.rating} out of 5."))
    if previous.review_count is not None and current.review_count is not None and current.review_count > previous.review_count:
        changes.append(("review_activity", f"New review activity recorded for {source.source_name}: {previous.review_count} to {current.review_count} reviews."))
    if previous.availability is not None and current.availability is not None and previous.availability != current.availability:
        changes.append(("source_availability", f"Source availability changed for {source.source_name}."))

    created = []
    watchers = db.query(SavedProduct).filter(SavedProduct.product_id == source.product_id).all()
    for watcher in watchers:
        for alert_type, message in changes:
            alert = Alert(
                user_id=watcher.user_id,
                product_id=source.product_id,
                alert_type=alert_type,
                message=message,
            )
            db.add(alert)
            created.append(alert)
    return created
