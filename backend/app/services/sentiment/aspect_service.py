import re
from typing import Dict, Any, List
from textblob import TextBlob
from app.services.sentiment.vader_service import VaderSentimentService

ASPECT_KEYWORDS = {
    "Camera": [
        "camera", "photo", "lens", "video", "sensor", "portrait", "selfie",
        "picture", "mp", "megapixel", "recording", "zoom", "night mode", "optics"
    ],
    "Battery": [
        "battery", "backup", "drain", "mah", "runtime", "endurance", "discharge",
        "screen on time", "sot", "standby"
    ],
    "Display": [
        "display", "screen", "amoled", "oled", "retina", "brightness", "refresh rate",
        "hz", "resolution", "bezel", "colors", "visuals", "panel", "viewing angle"
    ],
    "Performance": [
        "performance", "speed", "fast", "slow", "lag", "smooth", "processor",
        "chip", "chipset", "cpu", "gpu", "ram", "gaming", "multitasking", "stutter",
        "heat", "heating", "throttling"
    ],
    "Design": [
        "design", "look", "aesthetic", "appearance", "finish", "stylish", "sleek",
        "color", "form factor", "minimalist", "modern"
    ],
    "Build Quality": [
        "build quality", "build", "material", "sturdy", "solid", "plastic",
        "metal", "glass", "premium feel", "hinge", "creak", "craftsmanship"
    ],
    "Price": [
        "price", "cost", "value", "expensive", "affordable", "cheap", "worth",
        "pricing", "budget", "overpriced", "rupees", "deal", "investment"
    ],
    "Sound": [
        "sound", "audio", "speaker", "bass", "treble", "volume", "microphone",
        "mic", "clarity", "vocal", "noise cancellation", "anc", "acoustics", "headphone"
    ],
    "Comfort": [
        "comfort", "comfortable", "ergonomic", "fit", "pain", "earcups", "lightweight",
        "heavy", "wear", "grip", "hand feel", "snug"
    ],
    "Charging": [
        "charging", "charger", "fast charging", "wired", "wireless", "usb-c",
        "watt", "adapter", "juice up", "type-c"
    ],
    "Software": [
        "software", "os", "ui", "interface", "app", "bugs", "glitch", "updates",
        "bloatware", "firmware", "sync", "ecosystem", "android", "ios", "windows"
    ],
    "Durability": [
        "durability", "durable", "scratch", "drop", "waterproof", "water resistant",
        "ip68", "long-lasting", "robust", "tough", "wear and tear", "longevity"
    ],
}


class AspectSentimentService:
    def __init__(self):
        self.vader = VaderSentimentService()

    def _split_clauses(self, text: str) -> List[str]:
        # Split on sentence terminals and contrastive conjunctions
        pattern = r'[\.\?!;\n]+|\b(?:but|however|although|whereas|though|while|yet|on the other hand)\b'
        raw_clauses = re.split(pattern, text, flags=re.IGNORECASE)
        return [c.strip() for c in raw_clauses if c and len(c.strip()) > 3]

    def extract_aspects(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract aspect sentiment from review text.
        Returns a dict mapping aspect name to sentiment details.
        """
        if not text or not str(text).strip():
            return {}

        clauses = self._split_clauses(text)
        if not clauses:
            clauses = [text.strip()]

        detected_aspects: Dict[str, Dict[str, Any]] = {}

        for aspect_name, keywords in ASPECT_KEYWORDS.items():
            matching_clauses = []
            for clause in clauses:
                clause_lower = clause.lower()
                for kw in keywords:
                    # Check whole word match or keyword pattern
                    if re.search(r'\b' + re.escape(kw) + r'\b', clause_lower):
                        matching_clauses.append(clause)
                        break

            if matching_clauses:
                combined_clause_text = ". ".join(matching_clauses)
                vader_res = self.vader.analyze_text(combined_clause_text)
                blob = TextBlob(combined_clause_text)

                polarity = round(blob.sentiment.polarity, 4)
                subjectivity = round(blob.sentiment.subjectivity, 4)
                compound = round(vader_res["compound_score"], 4)

                if compound >= 0.05 or polarity > 0.15:
                    label = "positive"
                elif compound <= -0.05 or polarity < -0.15:
                    label = "negative"
                else:
                    label = "neutral"

                confidence = round(min(0.99, max(0.3, abs(compound) * 0.8 + abs(polarity) * 0.5 + 0.3)), 2)

                detected_aspects[aspect_name] = {
                    "sentiment": label,
                    "compound": compound,
                    "polarity": polarity,
                    "subjectivity": subjectivity,
                    "confidence": confidence,
                    "snippet": matching_clauses[0][:120],
                }

        return detected_aspects

    def compute_review_quality(self, text: str, rating: int, sentiment_label: str, verified_purchase: bool = True) -> float:
        """
        Calculate review quality score (0.0 to 1.0) based on length, detail, aspect presence, and consistency.
        """
        if not text:
            return 0.0

        length = len(text.strip())
        # Length score: <20 chars is 0.2, 50 chars is 0.6, >=120 chars is 1.0
        length_score = min(1.0, max(0.2, length / 120.0))

        # Detail score: presence of aspect keywords
        aspects = self.extract_aspects(text)
        aspect_score = min(1.0, 0.4 + (len(aspects) * 0.2))

        # Consistency score between star rating and sentiment label
        is_consistent = True
        if rating >= 4 and sentiment_label == "negative":
            is_consistent = False
        elif rating <= 2 and sentiment_label == "positive":
            is_consistent = False

        consistency_score = 1.0 if is_consistent else 0.4
        verified_bonus = 0.1 if verified_purchase else 0.0

        quality = (length_score * 0.4) + (aspect_score * 0.35) + (consistency_score * 0.25) + verified_bonus
        return round(min(1.0, max(0.1, quality)), 2)
