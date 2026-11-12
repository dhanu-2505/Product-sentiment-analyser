from app.services.scraper.base_scraper import BaseScraper


class FlipkartScraper(BaseScraper):
    def scrape(self, product_name: str):
        return {
            "product_name": product_name,
            "platform": "flipkart",
            "product_url": "https://www.flipkart.com/search?q=" + product_name.replace(" ", "%20"),
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
            "status": "unavailable",
            "message": "Live data unavailable for this source.",
            "reviews": [],
        }
