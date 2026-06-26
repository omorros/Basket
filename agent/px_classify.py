"""Bridge: the real Prometheux Classifier (Agent 3) into the pipeline.

Wraps the `classifier/` package (the Prometheux/Vadalog knowledge graph) and
returns `agent.schemas.ClassifiedReview` dataclasses so it is a drop-in for the
old regex stand-in `classify.classify_review`.

Uses the live engine when PMTX_TOKEN + a real JARVISPY_URL are set; otherwise
falls back to the deterministic in-Python MockPxClient so the pipeline still runs.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

from classifier.adapter import classify as _px_classify
from classifier.px_client import MockPxClient, RealPxClient
from classifier.seeds import DEMO_SEEDS, Seeds

from .schemas import Review, ClassifiedReview


def _engine_ready() -> bool:
    url = os.environ.get("JARVISPY_URL", "")
    return bool(os.environ.get("PMTX_TOKEN", "").strip()) and bool(url) and "{" not in url


def _seeds_for(reform_date: Optional[str]) -> Seeds:
    """Use the pipeline's reformulation date so engine + aggregator agree."""
    if not reform_date:
        return DEMO_SEEDS
    supersedes = [(new, old, reform_date) for (new, old, _) in DEMO_SEEDS.supersedes]
    return Seeds(aliases=DEMO_SEEDS.aliases, supersedes=supersedes, markers=DEMO_SEEDS.markers)


def classify_reviews(reviews: List[Review], reform_date: Optional[str]) -> List[ClassifiedReview]:
    seeds = _seeds_for(reform_date)
    dicts = [r.to_dict() for r in reviews]

    if _engine_ready():
        try:
            rows = _px_classify(dicts, seeds=seeds, client=RealPxClient())
            return [ClassifiedReview(**row) for row in rows]
        except Exception as e:  # auth/compute/network: degrade to mock, keep the run alive
            print(f"[prometheux] fell back to mock: {e}", file=sys.stderr)

    rows = _px_classify(dicts, seeds=seeds, client=MockPxClient())
    return [ClassifiedReview(**row) for row in rows]
