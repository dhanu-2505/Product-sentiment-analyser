from fastapi.testclient import TestClient

from app.database.database import Base
from app.main import app
from app.models import Product, ProductSource, Review, SentimentResult, SourceObservation
from app.sources.catalog import SUPPORTED_SOURCES
from tests.conftest import TestingSessionLocal, test_engine

client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def add_listing(session, product_name, source_code, platform="amazon", with_review=False):
    product = Product(
        name=product_name,
        brand="ReviewLens Demo",
        category="Electronics",
        platform=platform,
        is_demo=True,
    )
    session.add(product)
    session.flush()
    listing = ProductSource(product_id=product.id, source_name=source_code, data_type="seeded_demo")
    session.add(listing)
    session.flush()
    if with_review:
        review = Review(
            product_id=product.id,
            source_id=listing.id,
            reviewer_name=f"{source_code} demo reviewer",
            review_text="The display is clear and the performance feels smooth in daily use.",
            rating=5,
            source=source_code,
            is_demo=True,
            data_type="seeded_demo",
            verified_purchase=False,
        )
        session.add(review)
        session.flush()
        session.add(SentimentResult(review_id=review.id, sentiment_label="positive"))
    return product, listing


def test_all_configured_sources_match_only_their_source_listing():
    reset_db()
    session = TestingSessionLocal()
    try:
        for source in SUPPORTED_SOURCES:
            add_listing(session, f"Demo identity {source.code}", source.code, with_review=True)
        session.commit()
    finally:
        session.close()

    for source in SUPPORTED_SOURCES:
        response = client.post("/api/products/search", json={
            "query": f"Demo identity {source.code}",
            "source": source.code,
        })
        assert response.status_code == 200, (source.code, response.text)
        payload = response.json()
        assert payload["product"]["matched_source"] == source.code
        assert payload["product"]["source_data_type"] == "seeded_demo"
        assert payload["summary"]["total_reviews"] == 1
        assert payload["summary"]["positive_count"] == 1


def test_catalog_source_filter_is_applied_server_side():
    reset_db()
    session = TestingSessionLocal()
    try:
        myntra_product, _ = add_listing(session, "Nike Air Max", "myntra")
        add_listing(session, "Nike Air Max", "ajio")
        session.commit()
        expected_id = myntra_product.id
    finally:
        session.close()

    response = client.get("/api/products", params={"q": "Nike Air Max", "source": "myntra"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [expected_id]


def test_non_matching_source_returns_source_specific_empty_state_without_creating_product():
    reset_db()
    session = TestingSessionLocal()
    try:
        add_listing(session, "Babyhug Infant Car Seat", "firstcry", with_review=True)
        session.commit()
    finally:
        session.close()

    response = client.post("/api/products/search", json={"query": "iPhone 15", "source": "firstcry"})

    assert response.status_code == 404
    assert "No matching observation found" in response.json()["detail"]
    assert "FirstCry" in response.json()["detail"]
    assert client.get("/api/products", params={"q": "iPhone 15", "source": "firstcry"}).json()["count"] == 0


def test_vague_source_match_is_not_silently_treated_as_canonical_identity():
    reset_db()
    session = TestingSessionLocal()
    try:
        add_listing(session, "iPhone 15", "croma")
        session.commit()
    finally:
        session.close()

    response = client.post("/api/products/search", json={"query": "iPhone", "source": "croma"})

    assert response.status_code == 409
    assert "Potential match" in response.json()["detail"]
    assert "identity not verified" in response.json()["detail"]


def test_one_canonical_product_can_have_multiple_source_listings():
    reset_db()
    session = TestingSessionLocal()
    try:
        product, amazon = add_listing(session, "iPhone 15", "amazon", with_review=True)
        flipkart = ProductSource(product_id=product.id, source_name="flipkart", data_type="seeded_demo")
        session.add(flipkart)
        session.flush()
        session.add(SourceObservation(
            product_source_id=amazon.id,
            rating=4.3,
            review_count=5,
            data_type="seeded_demo",
        ))
        session.add(SourceObservation(
            product_source_id=flipkart.id,
            rating=4.1,
            review_count=4,
            data_type="seeded_demo",
        ))
        session.commit()
        product_id = product.id
    finally:
        session.close()

    amazon_result = client.post("/api/products/search", json={"query": "iPhone 15", "source": "amazon"})
    flipkart_result = client.post("/api/products/search", json={"query": "iPhone 15", "source": "flipkart"})
    source_rows = client.get(f"/api/products/{product_id}/sources").json()["items"]
    observed = {row["source"]: row for row in source_rows if row["status"] != "unavailable"}

    assert amazon_result.status_code == flipkart_result.status_code == 200
    assert amazon_result.json()["product"]["id"] == flipkart_result.json()["product"]["id"] == product_id
    assert {"amazon", "flipkart"} <= set(observed)
    assert observed["amazon"]["status"] == observed["flipkart"]["status"] == "seeded_demo"


def test_zero_review_source_does_not_create_sentiment_results():
    reset_db()
    session = TestingSessionLocal()
    try:
        product, _ = add_listing(session, "No review evidence product", "myntra")
        session.commit()
        product_id = product.id
    finally:
        session.close()

    response = client.post("/api/products/search", json={"query": "No review evidence product", "source": "myntra"})

    assert response.status_code == 200
    assert response.json()["summary"]["total_reviews"] == 0
    assert response.json()["summary"]["positive_count"] == 0
    session = TestingSessionLocal()
    try:
        assert session.query(Review).filter(Review.product_id == product_id).count() == 0
        assert session.query(SentimentResult).join(Review).filter(Review.product_id == product_id).count() == 0
    finally:
        session.close()


def test_selected_source_scopes_reviews_analytics_and_quality():
    reset_db()
    session = TestingSessionLocal()
    try:
        product, amazon = add_listing(session, "Source scoped phone", "amazon")
        flipkart = ProductSource(product_id=product.id, source_name="flipkart", data_type="seeded_demo")
        session.add(flipkart)
        session.flush()
        for source_record, source_code, sentiment, rating in (
            (amazon, "amazon", "positive", 5),
            (flipkart, "flipkart", "negative", 2),
        ):
            review = Review(
                product_id=product.id,
                source_id=source_record.id,
                reviewer_name=f"{source_code} reviewer",
                review_text=f"{source_code} source-specific evidence for this product.",
                rating=rating,
                source=source_code,
                is_demo=True,
                data_type="seeded_demo",
                verified_purchase=False,
            )
            session.add(review)
            session.flush()
            session.add(SentimentResult(review_id=review.id, sentiment_label=sentiment))
        session.commit()
        product_id = product.id
    finally:
        session.close()

    amazon_analytics = client.get(f"/api/products/{product_id}/analytics", params={"source": "amazon"})
    flipkart_analytics = client.get(f"/api/products/{product_id}/analytics", params={"source": "flipkart"})
    amazon_reviews = client.get(f"/api/products/{product_id}/reviews", params={"source": "amazon"})
    flipkart_quality = client.get(f"/api/products/{product_id}/review-quality", params={"source": "flipkart"})

    assert amazon_analytics.json()["total_reviews"] == 1
    assert amazon_analytics.json()["positive_count"] == 1
    assert flipkart_analytics.json()["total_reviews"] == 1
    assert flipkart_analytics.json()["negative_count"] == 1
    assert [review["source"] for review in amazon_reviews.json()["items"]] == ["amazon"]
    assert flipkart_quality.json()["review_count"] == 1


def test_source_demo_seed_is_idempotent_and_keeps_demo_provenance():
    from seed_products import seed_source_demo_evidence

    reset_db()
    session = TestingSessionLocal()
    try:
        inserted_first = seed_source_demo_evidence(session)
        session.commit()
        counts_after_first = (
            session.query(Product).count(),
            session.query(ProductSource).count(),
            session.query(Review).count(),
            session.query(SentimentResult).count(),
            session.query(SourceObservation).count(),
        )
        inserted_second = seed_source_demo_evidence(session)
        session.commit()
        counts_after_second = (
            session.query(Product).count(),
            session.query(ProductSource).count(),
            session.query(Review).count(),
            session.query(SentimentResult).count(),
            session.query(SourceObservation).count(),
        )
        assert inserted_first == 8
        assert inserted_second == 0
        assert counts_after_first == counts_after_second
        assert session.query(Review).filter(Review.data_type != "seeded_demo").count() == 0
        assert session.query(SourceObservation).filter(SourceObservation.data_type != "seeded_demo").count() == 0
        assert {row.source_name for row in session.query(ProductSource).all()} == {"myntra", "ajio"}
    finally:
        session.close()


def test_source_demo_seed_does_not_attach_synthetic_data_to_non_demo_product():
    from seed_products import seed_source_demo_evidence

    reset_db()
    session = TestingSessionLocal()
    try:
        product = Product(name="Existing live iPhone 15", brand="Apple", platform="amazon", is_demo=False)
        session.add(product)
        session.commit()
        product_id = product.id

        seed_source_demo_evidence(session)
        session.commit()

        assert session.query(ProductSource).filter_by(product_id=product_id).count() == 0
        assert session.query(Review).filter(Review.product_id == product_id).count() == 0
        assert session.query(Product).filter_by(id=product_id).one().is_demo is False
    finally:
        session.close()


def test_source_registry_does_not_claim_live_connectors():
    response = client.get("/api/sources")

    assert response.status_code == 200
    assert response.json()["count"] == 20
    connectors = {item["code"]: item["live_connector_configured"] for item in response.json()["items"]}
    assert connectors["amazon"] is True
    assert connectors["flipkart"] is True
    assert sum(connectors.values()) == 2
    assert all(item["status"] == "unavailable" for item in response.json()["items"])


def test_scraper_manager_never_substitutes_another_retailer(monkeypatch):
    from app.config import settings
    from app.services.scraper.scraper_manager import ScraperManager

    calls = []

    class FakeScraper:
        def __init__(self, result):
            self.result = result

        def scrape(self, query):
            calls.append(query)
            return self.result

    manager = ScraperManager()
    manager.scrapers = {
        "amazon": FakeScraper({"status": "unavailable"}),
        "flipkart": FakeScraper({"status": "live", "product_url": "https://store.test/item"}),
    }
    monkeypatch.setattr(settings, "use_mock_data", False)

    result = manager.scrape("iPhone 15", "amazon")

    assert calls == ["iPhone 15"]
    assert result["status"] == "unavailable"
    assert result["data_type"] == "unavailable"


def test_legacy_amazon_and_flipkart_platform_records_remain_searchable():
    reset_db()
    session = TestingSessionLocal()
    try:
        for source in ("amazon", "flipkart"):
            product = Product(name=f"Legacy {source} product", platform=source, is_demo=True)
            session.add(product)
            session.flush()
            session.add(Review(
                product_id=product.id,
                reviewer_name="Legacy demo review",
                review_text="A stored legacy review record for this listing.",
                rating=4,
                source="seed",
                is_demo=True,
                data_type="seeded_demo",
                verified_purchase=False,
            ))
        session.commit()
    finally:
        session.close()

    for source in ("amazon", "flipkart"):
        response = client.post("/api/products/search", json={"query": f"Legacy {source} product", "platform": source})
        assert response.status_code == 200, response.text
        assert response.json()["product"]["matched_source"] == source
        assert response.json()["summary"]["total_reviews"] == 1