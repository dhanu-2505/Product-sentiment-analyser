from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


database_url = normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


from sqlalchemy import inspect, text  # noqa: E402


def init_db() -> None:
    """Create all tables that don't exist yet (safe for incremental additions)."""
    Base.metadata.create_all(bind=engine)
    _safe_migrate_columns()


def _safe_migrate_columns() -> None:
    """Safely add new columns to existing tables without resetting or dropping database."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        # --- reviews table ---
        if "reviews" in inspector.get_table_names():
            review_cols = {col["name"] for col in inspector.get_columns("reviews")}
            if "verified_purchase" not in review_cols:
                conn.execute(text("ALTER TABLE reviews ADD COLUMN verified_purchase BOOLEAN DEFAULT 1"))

        # --- sentiment_results table ---
        if "sentiment_results" in inspector.get_table_names():
            sentiment_cols = {col["name"] for col in inspector.get_columns("sentiment_results")}
            for col_name, col_default in [
                ("polarity_score", "0.0"),
                ("subjectivity_score", "0.0"),
                ("confidence_score", "0.0"),
                ("quality_score", "1.0"),
            ]:
                if col_name not in sentiment_cols:
                    conn.execute(text(f"ALTER TABLE sentiment_results ADD COLUMN {col_name} FLOAT DEFAULT {col_default}"))
            if "aspects_json" not in sentiment_cols:
                conn.execute(text("ALTER TABLE sentiment_results ADD COLUMN aspects_json TEXT DEFAULT '{}'"))

        # --- search_history table ---
        if "search_history" in inspector.get_table_names():
            sh_cols = {col["name"] for col in inspector.get_columns("search_history")}
            if "product_id" not in sh_cols:
                conn.execute(text("ALTER TABLE search_history ADD COLUMN product_id INTEGER"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
