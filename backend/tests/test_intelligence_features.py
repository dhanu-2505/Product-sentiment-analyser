import json
import base64
import hashlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.database.database import Base
from app.models import Review
from tests.conftest import test_engine
from app.services.analytics.product_intelligence import compute_product_intelligence
from app.services.auth import hash_password, verify_password

client = TestClient(app)


def test_bcrypt_passwords_and_legacy_pbkdf2_hashes_verify():
    password = 'correct horse battery staple'
    bcrypt_hash = hash_password(password)
    assert bcrypt_hash.startswith('$2')
    assert verify_password(password, bcrypt_hash)
    assert not verify_password('wrong password', bcrypt_hash)

    salt = bytes(range(16))
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    legacy_hash = base64.b64encode(salt + derived).decode('utf-8')
    assert verify_password(password, legacy_hash)


def test_product_intelligence_uses_observed_evidence():
    review = SimpleNamespace(
        rating=4,
        verified_purchase=True,
        sentiment=SimpleNamespace(
            sentiment_label="positive",
            aspects_json=json.dumps({
                "Camera": {"sentiment": "positive"},
                "Price": {"sentiment": "negative"},
            }),
            quality_score=0.9,
        ),
    )

    result = compute_product_intelligence([review], 4.0, 1, 100, 0, 0)

    assert result["overall_score"] == result["intelligence_score"]
    assert result["breakdown"]["feature_satisfaction"]["score"] == 100.0
    assert result["breakdown"]["value_perception"]["score"] == 0.0
    assert 0 <= result["overall_score"] <= 100


def test_product_intelligence_has_no_score_without_reviews():
    result = compute_product_intelligence([])

    assert result["overall_score"] is None
    assert result["grade"] == "N/A"


def test_product_intelligence_excludes_aspects_without_evidence():
    review = SimpleNamespace(
        rating=4,
        verified_purchase=True,
        sentiment=SimpleNamespace(
            sentiment_label="positive",
            aspects_json="{}",
            quality_score=0.8,
        ),
    )

    result = compute_product_intelligence([review], 4.0, 1, 100, 0, 0)

    assert result["overall_score"] is not None
    assert result["breakdown"]["feature_satisfaction"]["score"] is None
    assert result["breakdown"]["value_perception"]["score"] is None
    assert "excluded from the score" in result["breakdown"]["value_perception"]["detail"]


def test_reports_are_user_scoped_and_csv_contains_database_rows():
    reset_db()
    registered = client.post('/api/auth/register', json={
        'name': 'Report User',
        'email': 'report-user@example.com',
        'password': 'secret123',
    })
    assert registered.status_code == 201
    headers = {'Authorization': f"Bearer {registered.json()['token']}"}

    search = client.post('/api/products/search', json={'query': 'Report workflow product', 'platform': 'amazon'})
    assert search.status_code == 200
    product_id = search.json()['product']['id']

    report_response = client.post('/api/reports', json={'product_id': product_id}, headers=headers)
    assert report_response.status_code == 200, report_response.text
    report_id = report_response.json()['id']
    assert report_response.json()['content']['summary']['total_reviews'] > 0
    assert 'review_quality' in report_response.json()['content']
    assert 'price_history' in report_response.json()['content']

    listed = client.get('/api/reports', headers=headers)
    assert listed.status_code == 200
    assert listed.json()['items'][0]['id'] == report_id
    detail = client.get(f'/api/reports/{report_id}', headers=headers)
    assert detail.status_code == 200
    assert detail.json()['content']['product_overview']['name'] == 'Report workflow product'
    pdf = client.get(f'/api/reports/{report_id}/download', headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers['content-type'] == 'application/pdf'

    export = client.get(f'/api/exports/reviews.csv?product_id={product_id}', headers=headers)
    assert export.status_code == 200
    assert 'text/csv' in export.headers['content-type']
    assert 'review_text' in export.text
    assert 'Report workflow product' in export.text

    empty_export = client.get('/api/exports/reviews.csv?product_id=999999', headers=headers)
    assert empty_export.status_code == 404

    other_user = client.post('/api/auth/register', json={
        'name': 'Other User',
        'email': 'other-report-user@example.com',
        'password': 'secret123',
    })
    other_headers = {'Authorization': f"Bearer {other_user.json()['token']}"}
    assert client.get(f'/api/reports/{report_id}', headers=other_headers).status_code == 404


def test_search_history_is_private_and_clear_is_user_scoped():
    reset_db()
    first = client.post('/api/auth/register', json={
        'name': 'History One', 'email': 'history-one@example.com', 'password': 'secret123',
    })
    second = client.post('/api/auth/register', json={
        'name': 'History Two', 'email': 'history-two@example.com', 'password': 'secret123',
    })
    first_headers = {'Authorization': f"Bearer {first.json()['token']}"}
    second_headers = {'Authorization': f"Bearer {second.json()['token']}"}

    client.post('/api/products/search', json={'query': 'iPhone 15', 'platform': 'amazon'}, headers=first_headers)
    client.post('/api/products/search', json={'query': 'MacBook Air M2', 'platform': 'amazon'}, headers=second_headers)

    first_history = client.get('/api/history', headers=first_headers)
    second_history = client.get('/api/history', headers=second_headers)
    assert first_history.status_code == second_history.status_code == 200
    assert len(first_history.json()['items']) == 1
    assert len(second_history.json()['items']) == 1
    assert first_history.json()['items'][0]['query'] == 'iPhone 15'
    assert second_history.json()['items'][0]['query'] == 'MacBook Air M2'
    assert client.get('/api/history').status_code == 401

    assert client.delete('/api/history', headers=first_headers).json()['count'] == 1
    assert client.get('/api/history', headers=first_headers).json()['count'] == 0
    assert client.get('/api/history', headers=second_headers).json()['count'] == 1


def test_sentiment_change_alert_requires_watchlist_and_uses_observed_snapshots():
    reset_db()
    registered = client.post('/api/auth/register', json={
        'name': 'Alert User', 'email': 'alert-user@example.com', 'password': 'secret123',
    })
    headers = {'Authorization': f"Bearer {registered.json()['token']}"}
    search = client.post('/api/products/search', json={'query': 'Alert evidence product', 'platform': 'amazon'})
    product_id = search.json()['product']['id']
    assert client.post('/api/watchlist', json={'product_id': product_id}, headers=headers).status_code == 200

    from tests.conftest import TestingSessionLocal
    session = TestingSessionLocal()
    try:
        reviews = session.query(Review).filter(Review.product_id == product_id).all()
        for review in reviews:
            review.sentiment.sentiment_label = 'negative'
        session.commit()
    finally:
        session.close()

    refreshed = client.post('/api/products/search', json={'query': 'Alert evidence product', 'platform': 'amazon'}, headers=headers)
    assert refreshed.status_code == 200
    alerts = client.get('/api/alerts', headers=headers)
    assert alerts.status_code == 200
    assert alerts.json()['count'] == 1
    assert alerts.json()['items'][0]['message'] == 'Sentiment change detected.'

    client.post('/api/products/search', json={'query': 'Alert evidence product', 'platform': 'amazon'}, headers=headers)
    assert client.get('/api/alerts', headers=headers).json()['count'] == 1


def test_source_observations_are_stored_and_trigger_measured_alerts():
    reset_db()
    registered = client.post('/api/auth/register', json={
        'name': 'Observation User', 'email': 'observation-user@example.com', 'password': 'secret123',
    })
    headers = {'Authorization': f"Bearer {registered.json()['token']}"}
    search = client.post('/api/products/search', json={'query': 'Observation fixture', 'platform': 'amazon'})
    product_id = search.json()['product']['id']
    assert client.post('/api/watchlist', json={'product_id': product_id}, headers=headers).status_code == 200

    baseline = client.post(f'/api/products/{product_id}/sources/amazon/observations', json={
        'price': 899.0, 'currency': 'INR', 'rating': 4.3, 'review_count': 100, 'availability': True,
    }, headers=headers)
    assert baseline.status_code == 201, baseline.text
    assert baseline.json()['status'] == 'stored'
    assert baseline.json()['alerts_created'] == 0

    changed = client.post(f'/api/products/{product_id}/sources/amazon/observations', json={
        'price': 849.0, 'currency': 'INR', 'rating': 4.5, 'review_count': 102, 'availability': False,
    }, headers=headers)
    assert changed.status_code == 201, changed.text
    assert changed.json()['alerts_created'] == 4
    alerts = client.get('/api/alerts', headers=headers)
    assert {item['alert_type'] for item in alerts.json()['items']} == {
        'price_change', 'rating_change', 'review_activity', 'source_availability',
    }
    assert all(item['message'] for item in alerts.json()['items'])


def reset_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def test_auth_and_saved_products_flow():
    reset_db()

    register = client.post('/api/auth/register', json={
        'name': 'Demo User',
        'email': 'demo@example.com',
        'password': 'secret123',
    })
    assert register.status_code == 201, register.text
    auth_data = register.json()
    assert 'token' in auth_data
    headers = {'Authorization': f"Bearer {auth_data['token']}"}
    profile = client.get('/api/profile', headers=headers)
    assert profile.status_code == 200
    assert profile.json()['search_count'] == 0
    updated = client.put('/api/profile', json={'name': 'Updated Demo User'}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()['name'] == 'Updated Demo User'

    product_search = client.post('/api/products/search', json={'query': 'boAt Rockerz 450', 'platform': 'amazon'})
    assert product_search.status_code == 200, product_search.text
    product_id = product_search.json()['product']['id']

    saved_response = client.post('/api/saved-products', json={'product_id': product_id}, headers={'Authorization': f"Bearer {auth_data['token']}"})
    assert saved_response.status_code == 201, saved_response.text
    assert saved_response.json()['product_id'] == product_id

    list_saved = client.get('/api/saved-products', headers={'Authorization': f"Bearer {auth_data['token']}"})
    assert list_saved.status_code == 200
    assert list_saved.json()['count'] >= 1


def test_compare_products_endpoint():
    reset_db()
    first = client.post('/api/products/search', json={'query': 'boAt Rockerz 450', 'platform': 'amazon'})
    second = client.post('/api/products/search', json={'query': 'Noise Cancelling Headphones', 'platform': 'amazon'})
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.post('/api/compare', json={'product_ids': [first.json()['product']['id'], second.json()['product']['id']]})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['count'] == 2
    assert 'items' in payload
    assert len(payload['items']) == 2
    assert all('price_data_type' in item and 'review_data_type' in item for item in payload['items'])
