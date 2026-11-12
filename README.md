# SentiLens — Product Intelligence Platform

SentiLens helps teams turn customer reviews into usable product intelligence. The app supports product searches, review collection, sentiment classification, analytics dashboards, saved-item workflows, and product comparisons.

## Overview

The project focuses on real product review analysis and customer voice extraction. It combines a FastAPI backend, a React frontend, SQLite-friendly local persistence, and a VADER-based sentiment pipeline to generate practical insights from product reviews.

## Features

- Product discovery and search
- Scraper-first review ingestion with mock fallback
- VADER sentiment scoring
- Review analytics and summary metrics
- Search history and saved-product tracking
- Product comparison endpoint and dashboard route
- Premium dark SaaS-style UI
- Auth flow with JWT-backed registration and login

## Architecture

- Frontend: React + Vite + Recharts
- Backend: FastAPI + SQLAlchemy
- Analytics: VADER + review aggregation logic
- Data: SQLite by default, PostgreSQL-ready configuration

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

```bash
cd frontend
npm run build
```

## Documentation

See the docs directory for architecture, API, sentiment, analytics, deployment, and scraping notes.

## Notes

This project is built for practical product intelligence workflows and supports a real analysis pipeline from product search through review sentiment and dashboard generation. Live scraping may be limited by site protections, so the fallback mock system is intentionally part of the same processing pipeline.
