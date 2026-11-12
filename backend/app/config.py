from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReviewLens - Product Sentiment Analyzer"
    environment: str = "development"
    database_url: str = "sqlite:///./product_sentiment.db"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    use_mock_data: bool = True
    scraper_timeout: int = 30
    scraper_headless: bool = True
    api_prefix: str = "/api"
    reports_dir: str = "./reports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
