"""Live pipeline → full RunResult JSON (the /run contract).

Real Tavily retrieval + Date-Finder (mine) wired through LOCAL stand-ins for
classify/aggregate (teammates' real Prometheux + ClickHouse drop in later).

CLI:  python -m agent.pipeline "Reese's Peanut Butter Cups"
Prints one JSON object matching ui/lib/types.ts:RunResult to stdout.
"""

from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

from .tavily_agent import retrieve_reviews, find_reformulation_date
from .px_classify import classify_reviews  # real Prometheux classifier (Agent 3)
from .aggregate import bucket_by_week, detect_inflection
from . import clickhouse_store as ch

load_dotenv()

# Fallback if the Date-Finder can't pin a date live (keeps the demo deterministic).
FALLBACK_DATES = {"reese's peanut butter cups": "2026-02-17"}


def run(product: str) -> dict:
    rd = find_reformulation_date(product)
    reform_date = rd.date or FALLBACK_DATES.get(product.lower())

    reviews = retrieve_reviews(product, sources=("news", "web"), max_results=20)
    classified = classify_reviews(reviews, reform_date)

    # Agent 4: real ClickHouse if configured, else the local stand-in.
    if ch.configured():
        try:
            buckets, inflection = ch.aggregate_and_detect(
                product.lower().strip(), classified, reform_date
            )
        except Exception as e:
            print(f"[clickhouse] fell back to local: {e}", file=sys.stderr)
            buckets = bucket_by_week(classified)
            inflection = detect_inflection(buckets, reform_date)
    else:
        buckets = bucket_by_week(classified)
        inflection = detect_inflection(buckets, reform_date)

    # Reviews for the UI: complaints with a date + a fired rule, newest first,
    # de-duplicated by excerpt (syndicated news repeats the same snippet).
    candidates = [c for c in classified if c.complaint_category != "none" and c.published_date]
    candidates.sort(key=lambda c: c.published_date or "", reverse=True)
    shown, seen_excerpts = [], set()
    for c in candidates:
        key = " ".join((c.raw_excerpt or "").lower().split())[:100]
        if key in seen_excerpts:
            continue
        seen_excerpts.add(key)
        shown.append(c)

    return {
        "product": product,
        "reformulation_date": inflection.reformulation_date,
        "reviews": [c.to_dict() for c in shown[:8]],
        "buckets": [b.__dict__ for b in buckets],
        "inflection": inflection.__dict__,
        # cited.md publish is Teammate B's Agent 5 — placeholder until the API is confirmed.
        "cited_url": "https://cited.md/r/reformulation-sentinel-"
        + product.lower().replace(" ", "-").replace("'", ""),
    }


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "Reese's Peanut Butter Cups"
    print(json.dumps(run(product)))
