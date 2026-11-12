# Deployment

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

## Production notes

- Frontend: deploy to Vercel
- Backend: deploy to Render
- Database: use PostgreSQL or Supabase Postgres in production
- Set environment variables for `database_url`, `frontend_url`, `secret_key`, and any scraper settings
