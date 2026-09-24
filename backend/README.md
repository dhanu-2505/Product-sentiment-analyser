# Backend README

This backend exposes the product sentiment analysis API and supports scraping, sentiment evaluation, analytics, and persistent storage.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API base

```text
http://localhost:8000
```

## Important notes

- Use `.env` for configuration.
- Keep scraping logic outside API route handlers.
- Do not bypass anti-bot protections or login restrictions.
