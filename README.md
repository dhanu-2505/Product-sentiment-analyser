# Product Sentiment Analyzer and Review Dashboard

A premium SaaS-style product intelligence dashboard for collecting ecommerce product reviews, analyzing sentiment, and visualizing customer feedback trends.

## Overview

This project helps users search products on Amazon and Flipkart, scrape available reviews, process them with NLP sentiment analysis, store results in PostgreSQL, and explore insights through an interactive dashboard.

## Features

- Search and analyze product sentiment across Amazon and Flipkart
- Review scraping with Selenium + BeautifulSoup
- VADER sentiment classification
- PostgreSQL persistence
- Dashboard analytics with charts and KPI cards
- Review explorer with filters and search
- Historical analysis tracking
- Production-ready backend architecture

## Tech Stack

### Frontend
- React + Vite
- JavaScript or TypeScript
- Tailwind CSS
- Recharts
- React Router

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Selenium
- BeautifulSoup
- VADER

## Project Structure

```text
product-sentiment-analyzer/
├── frontend/
├── backend/
├── data/
├── docs/
├── .gitignore
├── .env.example
├── README.md
└── .gitignore
```

## Environment Setup

1. Install Node.js 18+
2. Install Python 3.10+
3. Install PostgreSQL
4. Copy `.env.example` to `.env` and fill in values

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Setup

Create a PostgreSQL database named `product_sentiment` and update the `DATABASE_URL` in `.env`.

## Deployment Notes

- Frontend: Vercel or Netlify
- Backend: Render
- Database: Supabase PostgreSQL or any managed PostgreSQL service

## Scraping Limitations

This project uses Selenium for browser automation. Scraping should respect website terms, robots rules, and rate limits. If a site blocks scraping or returns a CAPTCHA, the app should use fallback/mock data for demo and testing.

## Future Enhancements

- Multi-platform expansion beyond Amazon and Flipkart
- NLP model comparison (VADER vs TextBlob vs transformer-based models)
- Automated alerts and reporting
- Historical trend forecasting
- Batch product analysis

## Status

Phase 1 project setup and folder structure are complete.
