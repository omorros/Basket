from typing import List, TypedDict


class Review(TypedDict):
    url: str
    source: str
    text: str
    published_date: str   # ISO 8601
    product_query: str


class ClassifiedReview(TypedDict):
    url: str
    variant_id: str
    complaint_category: str
    published_date: str
    rule_trace: List[str]
    raw_excerpt: str


VALID_CATEGORIES = {"taste", "texture", "packaging", "price", "none"}
CLASSIFIED_KEYS = {
    "url", "variant_id", "complaint_category",
    "published_date", "rule_trace", "raw_excerpt",
}


def validate_classified(row: dict) -> None:
    missing = CLASSIFIED_KEYS - row.keys()
    if missing:
        raise ValueError(f"ClassifiedReview missing keys: {sorted(missing)}")
    if row["complaint_category"] not in VALID_CATEGORIES:
        raise ValueError(f"bad complaint_category: {row['complaint_category']!r}")
    if not isinstance(row["rule_trace"], list):
        raise ValueError("rule_trace must be a list")
