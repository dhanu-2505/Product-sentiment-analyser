from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'


def test_product_search():
    response = client.post('/api/products/search?query=boAt%20Rockerz%20450&platform=amazon')
    assert response.status_code == 200
    assert response.json()['product']['name'] == 'boAt Rockerz 450'


def test_sentiment_analysis():
    response = client.post('/api/sentiment/analyze', json={'text': 'This product is excellent and works very well.'})
    assert response.status_code == 200
    assert 'sentiment_label' in response.json()
