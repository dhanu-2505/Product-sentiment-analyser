from __future__ import annotations

from datetime import datetime, timedelta
from random import Random


REVIEWER_NAMES = [
    "Aarav", "Meera", "Nikhil", "Priya", "Rohan", "Ananya", "Karan", "Ishita",
    "Vikram", "Neha", "Aditya", "Sanya", "Rohit", "Diya", "Shivam", "Tanvi",
    "Harsh", "Pooja", "Kabir", "Aisha", "Yash", "Mira", "Divya", "Rahul",
    "Sonia", "Ritika", "Aman", "Sneha", "Mohit", "Kavya", "Jay",
]

POSITIVE_TEXT = [
    "Absolutely love this product. The sound quality is excellent and the battery lasts all day.",
    "The build feels premium and the performance is really reliable. Highly recommended.",
    "Comfortable to wear for long hours and the audio clarity is superb.",
    "This product exceeded my expectations. Great value for money and very easy to use.",
    "Battery life is outstanding and the bass is punchy without distorting sound.",
]

NEUTRAL_TEXT = [
    "The product works as expected and feels decent for everyday use.",
    "Overall it is okay. Sound quality is fine, but nothing extraordinary.",
    "It is a reasonable purchase with average battery performance and good enough sound.",
    "The device is functional and meets basic needs, though some features feel average.",
    "Useful product with minor trade-offs. Works consistently but not memorable.",
]

NEGATIVE_TEXT = [
    "Very poor quality and disappointing overall. The performance is not worth the price.",
    "Battery drains too fast and the sound is weak compared to alternatives.",
    "I had connectivity issues and the build feels cheap after a few days of use.",
    "The product is uncomfortable to wear for long periods and not durable enough.",
    "This was a frustrating purchase. Features do not work as advertised.",
]


def _rating_for_sentiment(sentiment: str, rng: Random) -> int:
    if sentiment == "positive":
        return rng.choice([4, 5, 5, 4, 5])
    if sentiment == "negative":
        return rng.choice([1, 2, 2, 3, 1])
    return rng.choice([3, 3, 4, 2, 3])


def generate_mock_product(product_name: str, platform: str = "amazon") -> dict:
    normalized_name = (product_name or "Sample Product").strip() or "Sample Product"
    normalized_platform = (platform or "amazon").strip().lower() or "amazon"
    rng = Random(abs(hash(normalized_name.lower() + normalized_platform)) % 1000000)

    reviews = []
    sentiment_sequence = ["positive", "neutral", "negative"]
    for index in range(30):
        sentiment = sentiment_sequence[index % len(sentiment_sequence)]
        if index in (0, 1, 2, 3, 4, 5, 8, 10, 12):
            sentiment = "positive"
        elif index % 7 == 0:
            sentiment = "negative"
        elif index % 5 == 0:
            sentiment = "neutral"

        if sentiment == "positive":
            text = rng.choice(POSITIVE_TEXT)
        elif sentiment == "negative":
            text = rng.choice(NEGATIVE_TEXT)
        else:
            text = rng.choice(NEUTRAL_TEXT)

        review_date = datetime.utcnow() - timedelta(days=29 - index)
        reviews.append(
            {
                "reviewer_name": rng.choice(REVIEWER_NAMES),
                "review_text": text,
                "rating": _rating_for_sentiment(sentiment, rng),
                "review_date": review_date.isoformat(),
            }
        )

    average_rating = round(sum(item["rating"] for item in reviews) / len(reviews), 2)
    return {
        "product_name": normalized_name,
        "platform": normalized_platform,
        "product_url": f"https://www.{normalized_platform}.com/search?q={normalized_name.replace(' ', '+')}",
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
        "rating": average_rating,
        "reviews": reviews,
    }
