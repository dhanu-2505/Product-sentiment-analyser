from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.database import init_db
from app.routes import analytics, auth, compare, history, products, reports, reviews, saved, scrape, sentiment, sources

app = FastAPI(
    title="Product Sentiment Analyzer",
    description="Analyze customer sentiment and product performance from ecommerce reviews.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(sentiment.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(scrape.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(saved.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(sources.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "Product Sentiment Analyzer API"}
