from app.config import settings
from app.services.mock_data import generate_mock_product
from app.services.scraper.amazon_scraper import AmazonScraper
from app.services.scraper.flipkart_scraper import FlipkartScraper


class ScraperManager:
    def __init__(self, timeout: int = 30, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.scrapers = {
            "amazon": AmazonScraper(timeout=timeout, headless=headless),
            "flipkart": FlipkartScraper(timeout=timeout, headless=headless),
        }

    def scrape(self, product_name: str, platform: str = "amazon"):
        if not product_name or not str(product_name).strip():
            raise ValueError("Product name is required")

        platform_key = (platform or "amazon").strip().lower()
        scraper = self.scrapers.get(platform_key)
        if scraper is not None:
            try:
                data = scraper.scrape(product_name)
                if data and data.get("status") == "live":
                    data.setdefault("data_type", "live_scraped")
                    return data
            except Exception:
                pass

        if settings.use_mock_data:
            fallback = generate_mock_product(product_name, platform_key)
            fallback.update(
                {
                    "source": "seeded_demo",
                    "data_type": "seeded_demo",
                    "status": "seeded_demo",
                    "review_count": len(fallback.get("reviews", [])),
                    "message": "Synthetic seeded demo data; no live source data was obtained.",
                }
            )
            return fallback

        return {
            "source": platform_key,
            "data_type": "unavailable",
            "status": "unavailable",
            "message": "Live data unavailable for this source.",
            "reviews": [],
        }

    def scrape_product(self, product_name: str, platform: str = "amazon"):
        return self.scrape(product_name, platform)
