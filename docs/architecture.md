# Architecture

SentiLens is built as a small but production-oriented full-stack product intelligence platform.

## High-level flow

1. User searches a product or opens a saved product.
2. Product scraper or mock fallback retrieves normalized product metadata and reviews.
3. FastAPI routes persist the product, review, and sentiment result records.
4. Analytics service computes summary metrics, rating distribution, trends, and keyword frequency.
5. Frontend dashboard renders the real analytics data for product discovery and review exploration.

## Backend

- FastAPI application in `backend/app`
- SQLAlchemy ORM with SQLite by default and PostgreSQL-ready connection string support
- A service layer for scraper, sentiment, analytics, and auth

## Frontend

- React + Vite app in `frontend/src`
- Route-based navigation for search, dashboard, compare, saved products, reports, settings, and history
- Recharts-driven visual analytics

## Data model

Core entities are `Product`, `Review`, `SentimentResult`, `AnalysisHistory`, `User`, `SavedProduct`, and `SearchHistory`.
