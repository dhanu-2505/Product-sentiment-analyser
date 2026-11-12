from __future__ import annotations

import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Any, Iterable


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"\w+", (text or "").lower()))


def analyze_review_patterns(reviews: Iterable[Any]) -> dict:
    review_list = list(reviews)
    if not review_list:
        return {
            "review_count": 0,
            "coverage": "insufficient_data",
            "signals": [],
            "summary": "Insufficient review data to assess patterns.",
        }

    signals = []
    by_text: dict[str, list[int]] = defaultdict(list)
    by_day: dict[str, list[int]] = defaultdict(list)
    rating_counts = Counter()
    short_review_ids = []

    for review in review_list:
        normalized = _normalize(review.review_text)
        if normalized:
            by_text[normalized].append(review.id)
        if len((review.review_text or "").strip()) < 20:
            short_review_ids.append(review.id)
        if review.rating is not None:
            rating_counts[int(review.rating)] += 1
        if review.review_date:
            by_day[review.review_date.date().isoformat()].append(review.id)

    duplicate_groups = [ids for ids in by_text.values() if len(ids) > 1]
    if duplicate_groups:
        signals.append({
            "type": "repeated_text",
            "level": "similarity_signal",
            "message": "Identical normalized review wording appears more than once.",
            "group_count": len(duplicate_groups),
            "review_ids": [review_id for group in duplicate_groups for review_id in group],
        })

    unique_texts = [(text, ids) for text, ids in by_text.items() if len(text.split()) >= 5]
    similar_pairs = []
    for index, (left_text, left_ids) in enumerate(unique_texts[:500]):
        left_words = set(left_text.split())
        for right_text, right_ids in unique_texts[index + 1:500]:
            right_words = set(right_text.split())
            union = left_words | right_words
            overlap = len(left_words & right_words) / len(union) if union else 0
            if overlap >= 0.85 and SequenceMatcher(None, left_text, right_text).ratio() >= 0.82:
                similar_pairs.append((left_ids[0], right_ids[0]))
                if len(similar_pairs) >= 100:
                    break
        if len(similar_pairs) >= 100:
            break
    if similar_pairs:
        signals.append({
            "type": "similar_wording",
            "level": "similarity_signal",
            "message": "Some reviews contain highly similar wording; this is a pattern signal, not a conclusion about authenticity.",
            "pair_count": len(similar_pairs),
            "review_id_pairs": similar_pairs,
        })

    if short_review_ids:
        signals.append({
            "type": "very_short_text",
            "level": "quality_signal",
            "message": "Some review texts contain fewer than 20 characters and provide limited detail.",
            "count": len(short_review_ids),
            "review_ids": short_review_ids[:100],
        })

    total_ratings = sum(rating_counts.values())
    if total_ratings >= 10:
        common_rating, common_count = rating_counts.most_common(1)[0]
        share = common_count / total_ratings
        if share >= 0.85:
            signals.append({
                "type": "rating_concentration",
                "level": "concentration_signal",
                "message": f"A single rating ({common_rating} stars) represents {share:.0%} of this review sample.",
                "rating": common_rating,
                "share": round(share, 3),
                "sample_size": total_ratings,
            })

    largest_day = max(by_day.items(), key=lambda entry: len(entry[1]), default=None)
    if largest_day and total_ratings >= 10 and len(largest_day[1]) >= 10 and len(largest_day[1]) / len(review_list) >= 0.5:
        signals.append({
            "type": "timing_concentration",
            "level": "timing_signal",
            "message": f"Many review dates cluster on {largest_day[0]}; timing alone does not establish a cause.",
            "date": largest_day[0],
            "count": len(largest_day[1]),
            "review_ids": largest_day[1][:100],
        })

    return {
        "review_count": len(review_list),
        "coverage": "analyzed_first_500_unique_texts" if len(unique_texts) > 500 else "analyzed_all",
        "signals": signals,
        "summary": "No configured pattern signals found in this sample." if not signals else "Pattern signals require human review and do not determine review authenticity.",
    }
