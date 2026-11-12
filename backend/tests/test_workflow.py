from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.models import Product
from app.services.analytics.review_quality import analyze_review_patterns
from types import SimpleNamespace
from datetime import datetime
from app.database.database import Base
from tests.conftest import test_engine

client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_health_and_product_search():
    reset_db()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

    search = client.post('/api/products/search', json={'query': 'boAt Rockerz 450', 'platform': 'amazon'})
    assert search.status_code == 200
    assert search.json()['product']['name'] == 'boAt Rockerz 450'
    assert search.json()['product']['platform'] == 'amazon'


def test_vader_sentiment_for_positive_negative_and_neutral():
    reset_db()

    positive = client.post('/api/sentiment/analyze', json={'text': 'I absolutely love this product. Excellent quality!'})
    assert positive.status_code == 200
    assert positive.json()['sentiment_label'] == 'positive'
    assert positive.json()['compound_score'] > 0.05

    negative = client.post('/api/sentiment/analyze', json={'text': 'Very poor quality. Completely disappointed.'})
    assert negative.status_code == 200
    assert negative.json()['sentiment_label'] == 'negative'
    assert negative.json()['compound_score'] < -0.05

    neutral = client.post('/api/sentiment/analyze', json={'text': 'The product is average and does what it says.'})
    assert neutral.status_code == 200
    assert neutral.json()['sentiment_label'] == 'neutral'
    assert abs(neutral.json()['compound_score']) <= 0.05


def test_mock_data_and_analytics_workflow():
    reset_db()
    search = client.post('/api/products/search', json={'query': 'Noise Cancelling Headphones', 'platform': 'amazon'})
    assert search.status_code == 200
    product = search.json()['product']

    reviews = client.get(f"/api/products/{product['id']}/reviews")
    assert reviews.status_code == 200
    payload = reviews.json()
    assert payload['count'] >= 1
    assert payload['items'][0]['data_type'] in {'seeded_demo', 'live_scraped'}

    analytics = client.get(f"/api/products/{product['id']}/analytics")
    assert analytics.status_code == 200
    assert analytics.json()['total_reviews'] >= 1
    assert 'rating_distribution' in analytics.json()

    word_frequency = client.get(f"/api/products/{product['id']}/word-frequency")
    assert word_frequency.status_code == 200
    assert len(word_frequency.json()['words']) >= 1


def test_invalid_and_error_handling():
    reset_db()
    empty = client.post('/api/sentiment/analyze', json={'text': '   '})
    assert empty.status_code == 400

    missing = client.get('/api/products/999')
    assert missing.status_code == 404

    invalid_platform = client.post('/api/products/search', json={'query': 'abc', 'platform': 'invalid'})
    assert invalid_platform.status_code == 400

    product = client.post('/api/scrape/analyze', json={'product_name': 'Sample product'})
    assert product.status_code == 200
    assert product.json()['status'] == 'seeded_demo'
    assert product.json()['data_type'] == 'seeded_demo'


def test_source_catalog_reports_unavailable_without_fabricated_values():
    reset_db()
    catalog = client.get('/api/sources')
    assert catalog.status_code == 200
    assert catalog.json()['count'] == 20

    search = client.post('/api/products/search', json={'query': 'Source check product', 'platform': 'amazon'})
    assert search.status_code == 200
    product_id = search.json()['product']['id']
    response = client.get(f'/api/products/{product_id}/sources')

    assert response.status_code == 200
    assert response.json()['count'] == 20
    sources = {item['source']: item for item in response.json()['items']}
    assert sources['amazon']['status'] == 'seeded_demo'
    assert sources['amazon']['price'] is None
    assert sources['amazon']['checked'] is False
    assert all(item['status'] == 'unavailable' for source, item in sources.items() if source != 'amazon')
    assert all(item['price'] is None and item['rating'] is None for source, item in sources.items() if source != 'amazon')


def test_unavailable_live_search_does_not_create_a_product(monkeypatch):
    reset_db()
    monkeypatch.setattr(settings, 'use_mock_data', False)

    response = client.post('/api/products/search', json={'query': 'Unavailable live product', 'platform': 'amazon'})

    assert response.status_code == 503
    assert response.json()['detail'] == 'Live data unavailable for this source.'
    from tests.conftest import TestingSessionLocal
    session = TestingSessionLocal()
    try:
        assert session.query(Product).filter(Product.name == 'Unavailable live product').count() == 0
    finally:
        session.close()


def test_review_explorer_filters_and_server_pagination():
    reset_db()
    search = client.post('/api/products/search', json={'query': 'Review filter fixture', 'platform': 'amazon'})
    product_id = search.json()['product']['id']

    filtered = client.get(
        f'/api/products/{product_id}/reviews',
        params={'source': 'amazon', 'data_type': 'seeded_demo', 'verified_purchase': 'false', 'page': 1, 'limit': 5},
    )
    assert filtered.status_code == 200
    assert filtered.json()['count'] <= 5
    assert filtered.json()['total'] > filtered.json()['count']
    assert all(item['source'] == 'amazon' and item['data_type'] == 'seeded_demo' and not item['verified_purchase'] for item in filtered.json()['items'])

    later = client.get(f'/api/products/{product_id}/reviews', params={'start_date': '2099-01-01T00:00:00'})
    assert later.status_code == 200
    assert later.json()['total'] == 0

    confidence_sorted = client.get(f'/api/products/{product_id}/reviews', params={'sort': 'confidence', 'limit': 10})
    assert confidence_sorted.status_code == 200
    scores = [item['confidence'] for item in confidence_sorted.json()['items']]
    assert scores == sorted(scores, reverse=True)


def test_review_pattern_signals_are_cautious_and_data_based():
    reviews = [
        SimpleNamespace(id=index, review_text='Excellent quality and very comfortable to use every day.', rating=5, review_date=datetime(2026, 9, 20))
        for index in range(10)
    ]
    reviews.append(SimpleNamespace(id=11, review_text='ok', rating=5, review_date=datetime(2026, 9, 20)))

    result = analyze_review_patterns(reviews)
    signal_types = {signal['type'] for signal in result['signals']}

    assert {'repeated_text', 'very_short_text', 'rating_concentration', 'timing_concentration'} <= signal_types
    assert 'authenticity' in result['summary']
    assert analyze_review_patterns([])['coverage'] == 'insufficient_data'


def test_review_quality_endpoint_returns_aggregate_signals():
    reset_db()
    search = client.post('/api/products/search', json={'query': 'Review quality endpoint fixture', 'platform': 'amazon'})
    product_id = search.json()['product']['id']

    response = client.get(f'/api/products/{product_id}/review-quality')

    assert response.status_code == 200
    assert response.json()['review_count'] > 0
    assert response.json()['coverage'] == 'analyzed_all'
    assert all('fake' not in signal['message'].lower() for signal in response.json()['signals'])
