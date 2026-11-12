# API reference

## Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

## Products

- `GET /api/products`
- `GET /api/products/{product_id}`
- `POST /api/products/search`
- `GET /api/products/{product_id}/analytics`
- `GET /api/products/{product_id}/reviews`

## Sentiment and insight endpoints

- `POST /api/sentiment/analyze`
- `GET /api/products/{product_id}/word-frequency`
- `POST /api/compare`
- `POST /api/saved-products`
- `GET /api/saved-products`
- `POST /api/reports`

## Utility

- `GET /health`
- `POST /scrape`
- `POST /scrape/analyze`
