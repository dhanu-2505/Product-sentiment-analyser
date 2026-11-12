from __future__ import annotations

from abc import ABC, abstractmethod


class PlatformAdapter(ABC):
    name = "base"

    @abstractmethod
    def normalize_product(self, product_name: str, data: dict):
        raise NotImplementedError

    @abstractmethod
    def normalize_review(self, review: dict):
        raise NotImplementedError


class AmazonAdapter(PlatformAdapter):
    name = "amazon"

    def normalize_product(self, product_name: str, data: dict):
        return {
            "name": data.get("name") or product_name,
            "brand": data.get("brand") or "Amazon",
            "category": data.get("category") or "Consumer electronics",
            "product_url": data.get("product_url") or f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}",
            "image_url": data.get("image_url") or "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
            "price": data.get("price", 0),
            "currency": data.get("currency", "INR"),
            "rating": float(data.get("rating", 0) or 0),
            "review_count": int(data.get("review_count", 0) or 0),
        }

    def normalize_review(self, review: dict):
        return {
            "reviewer_name": review.get("reviewer_name") or "Anonymous",
            "review_title": review.get("review_title") or "Customer review",
            "review_text": review.get("review_text") or "",
            "rating": int(review.get("rating", 3) or 3),
            "review_date": review.get("review_date"),
            "verified_purchase": bool(review.get("verified_purchase", False)),
        }


class FlipkartAdapter(PlatformAdapter):
    name = "flipkart"

    def normalize_product(self, product_name: str, data: dict):
        return {
            "name": data.get("name") or product_name,
            "brand": data.get("brand") or "Flipkart",
            "category": data.get("category") or "Electronics",
            "product_url": data.get("product_url") or f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}",
            "image_url": data.get("image_url") or "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
            "price": data.get("price", 0),
            "currency": data.get("currency", "INR"),
            "rating": float(data.get("rating", 0) or 0),
            "review_count": int(data.get("review_count", 0) or 0),
        }

    def normalize_review(self, review: dict):
        return {
            "reviewer_name": review.get("reviewer_name") or "Anonymous",
            "review_title": review.get("review_title") or "Customer review",
            "review_text": review.get("review_text") or "",
            "rating": int(review.get("rating", 3) or 3),
            "review_date": review.get("review_date"),
            "verified_purchase": bool(review.get("verified_purchase", False)),
        }


def get_platform_adapter(platform: str):
    adapters = {
        "amazon": AmazonAdapter(),
        "flipkart": FlipkartAdapter(),
    }
    return adapters.get((platform or "amazon").lower(), AmazonAdapter())
