from typing import List
from classifier.adapter import classify


def classified_payload(reviews: List[dict]) -> dict:
    """The classifier's slice of the GET /run response (see TEAM.md)."""
    return {"reviews": classify(reviews)}
