from app.services.scraper.base_scraper import BaseScraper


class AmazonScraper(BaseScraper):
    def scrape(self, product_name: str):
        return {
            "platform": "amazon",
            "status": "unavailable",
            "message": "Live data unavailable for this source.",
            "reviews": [],
        }
