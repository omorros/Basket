"""LOCAL STAND-IN for the ClickHouse Aggregator/Detector (Agent 4).

Teammate B/C replaces this with the real week×category SQL + inflection query.
Output shapes (WeeklyBucket, Inflection) are the frozen contract.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from .schemas import ClassifiedReview, WeeklyBucket, Inflection


def _week_start(iso: str) -> str:
    """Monday of the ISO week containing `iso` (YYYY-MM-DD)."""
    y, m, d = (int(x) for x in iso.split("-"))
    dt = date(y, m, d)
    return (dt - timedelta(days=dt.weekday())).isoformat()


def bucket_by_week(reviews: list[ClassifiedReview]) -> list[WeeklyBucket]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for r in reviews:
        if not r.published_date or r.complaint_category == "none":
            continue
        counts[(_week_start(r.published_date), r.complaint_category)] += 1
    return [
        WeeklyBucket(week=w, complaint_category=c, count=n)
        for (w, c), n in sorted(counts.items())
    ]


def detect_inflection(
    buckets: list[WeeklyBucket], reformulation_date: Optional[str]
) -> Inflection:
    """Heaviest complaint week at/after the reformulation vs the pre-baseline."""
    totals: dict[str, int] = defaultdict(int)
    for b in buckets:
        totals[b.week] += b.count
    if not totals:
        return Inflection(inflection_week="", reformulation_date=reformulation_date or "", severity=0.0)

    ref = reformulation_date or min(totals)
    pre = [n for w, n in totals.items() if w < ref]
    baseline = (sum(pre) / len(pre)) if pre else 0.0
    post = {w: n for w, n in totals.items() if w >= ref} or totals
    peak_week = max(post, key=lambda w: post[w])
    severity = round(post[peak_week] / max(baseline, 1.0), 2)
    return Inflection(
        inflection_week=peak_week,
        reformulation_date=ref,
        severity=severity,
    )
