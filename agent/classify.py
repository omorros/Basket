"""LOCAL STAND-IN for the Prometheux Classifier (Agent 3).

Teammate C replaces this with real declarative rules + entity resolution.
Until then this gives the UI a real rule_trace from live data. The OUTPUT
shape (ClassifiedReview) is the frozen contract, so the swap is drop-in.
"""

from __future__ import annotations

import re
from typing import Optional

from .schemas import Review, ClassifiedReview

# (category, rule-id, marker regex) — ordered by priority.
RULES = [
    ("texture", "R2-texture", r"waxy|gritty|chalky|compound coating|not real chocolate|texture"),
    ("taste",   "R1-taste",   r"tastes? different|changed (?:the |its )?recipe|worse|chemical|bland|cheap(?:er|ened)"),
    ("packaging", "R4-packaging", r"packag|wrapper|smaller|shrunk|shrink"),
    ("price",   "R6-price",   r"price|expensive|shrinkflation|cost more"),
]
_RESOLUTION = r"shift back|classic recipe|revers|bring back|going back"


def classify_review(rv: Review, reformulation_date: Optional[str]) -> ClassifiedReview:
    text = rv.text or ""
    low = text.lower()
    trace: list[str] = []
    category = "none"

    # company-reaction reviews are not complaints — tag and exclude from the spike
    if re.search(_RESOLUTION, low):
        trace.append("R5-resolution: company-reaction marker matched")
        category = "none"
    else:
        for cat, rid, pat in RULES:
            m = re.search(pat, low)
            if m:
                trace.append(f"{rid}: matched /{pat.split('|')[0]}.../ on \"{m.group(0)}\"")
                if category == "none":
                    category = cat

    # date-relative rule (the explainable one judges love)
    if reformulation_date and rv.published_date:
        if rv.published_date >= reformulation_date:
            trace.append(
                f"R7-date-relative: published {rv.published_date} ≥ "
                f"reformulation {reformulation_date} → post-reformulation"
            )
            if category != "none":
                trace.append(f"→ classified PostReformulation{category.capitalize()}Complaint")
        else:
            trace.append(
                f"R7-date-relative: published {rv.published_date} < "
                f"reformulation {reformulation_date} → pre-reformulation baseline"
            )

    return ClassifiedReview(
        url=rv.url,
        variant_id="reeses-pbc-standard",  # entity-resolution stub (Prometheux's job)
        complaint_category=category,
        published_date=rv.published_date,
        rule_trace=trace or ["no rule fired"],
        raw_excerpt=text[:200].strip(),
    )
