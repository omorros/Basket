"""
Orchestrator — Agent 0
GET /run?product=<name>

Drives the full pipeline:
  Agent 1 (Date-Finder, Tavily) -> Agent 2 (Retrieval, Tavily)
  -> Agent 3 (Classifier) -> Agent 4 (ClickHouse aggregate + detect)
  -> inflection check -> Agent 5 (Publisher, Senso)

Returns the full /run contract shape consumed by the Next.js UI.

Run with:
  uvicorn orchestrator:app --reload --port 8000
"""

import os
import sys

from dotenv import load_dotenv

# Load .env BEFORE importing publisher (it reads SENSO_API_KEY at import time).
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Our validated agents (Tavily + ClickHouse + classifier).
from agent.tavily_agent import find_reformulation_date, retrieve_reviews
from agent.classify import classify_review
from agent import clickhouse_store as ch
from agent.aggregate import bucket_by_week, detect_inflection as local_detect

# Teammate's Senso publisher (Agent 5).
from publisher import publish_alert, publish_alert_stub

# ── Config ──────────────────────────────────────────────────────────────────
USE_STUB_PUBLISHER = os.environ.get("USE_STUB_PUBLISHER", "true").lower() == "true"
# Flip to true once C's Prometheux classifier.classify() is live + Reese's-aware.
USE_REAL_CLASSIFIER = os.environ.get("USE_REAL_CLASSIFIER", "false").lower() == "true"
# Threshold below which we don't bother publishing an alert.
PUBLISH_MIN_SEVERITY = 1.2
# Keeps the demo deterministic if the Date-Finder can't pin a date live.
FALLBACK_DATES = {"reese's peanut butter cups": "2026-02-17"}

app = FastAPI(title="Reformulation Sentinel — Orchestrator")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def _classify(review_objs, reformulation_date) -> list:
    """Agent 3. Prometheux (live engine or its Reese's mock) when enabled,
    else our local regex rules."""
    if USE_REAL_CLASSIFIER:
        try:
            from agent.px_classify import classify_reviews
            out = classify_reviews(review_objs, reformulation_date)
            print(f"[orchestrator] Agent 3: Prometheux classified {len(out)}")
            return out
        except Exception as e:
            print(f"[orchestrator] Prometheux failed ({e}); using local classifier")
    return [classify_review(r, reformulation_date) for r in review_objs]


def _dedupe_for_ui(classified: list, limit: int = 8) -> list:
    """Newest-first, de-duplicated by excerpt (syndicated news repeats snippets)."""
    rows = [c for c in classified if c.complaint_category != "none" and c.published_date]
    rows.sort(key=lambda c: c.published_date or "", reverse=True)
    out, seen = [], set()
    for c in rows:
        key = " ".join((c.raw_excerpt or "").lower().split())[:100]
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out[:limit]


@app.get("/run")
async def run(product: str = Query(..., description="Product name to analyse")):
    print(f"\n[orchestrator] === pipeline for '{product}' ===")

    # ── Agent 1: Date-Finder ─────────────────────────────────────────────────
    # For the validated demo product we anchor to the confirmed date so the live
    # demo is deterministic; the Date-Finder still runs live for any other product.
    known = FALLBACK_DATES.get(product.lower().strip())
    try:
        rd = find_reformulation_date(product)
        reformulation_date = known or rd.date
    except Exception as e:
        print(f"[orchestrator] Agent 1 failed: {e}")
        reformulation_date = known
    print(f"[orchestrator] reformulation_date = {reformulation_date}")

    # ── Agent 2: Retrieval ───────────────────────────────────────────────────
    try:
        review_objs = retrieve_reviews(product, sources=("news", "web"), max_results=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")
    print(f"[orchestrator] retrieved {len(review_objs)} reviews")
    if not review_objs:
        raise HTTPException(status_code=404, detail=f"No mentions found for '{product}'.")

    # ── Agent 3: Classifier (Prometheux when enabled, else our local rules) ──
    classified = _classify(review_objs, reformulation_date)

    # ── Agent 4: ClickHouse aggregate + detect (local fallback) ──────────────
    pid = product.lower().strip()
    if ch.configured():
        try:
            bucket_objs, infl = ch.aggregate_and_detect(pid, classified, reformulation_date)
        except Exception as e:
            print(f"[orchestrator] ClickHouse fell back to local: {e}")
            bucket_objs = bucket_by_week(classified)
            infl = local_detect(bucket_objs, reformulation_date)
    else:
        bucket_objs = bucket_by_week(classified)
        infl = local_detect(bucket_objs, reformulation_date)

    buckets = [b.__dict__ for b in bucket_objs]
    inflection = infl.__dict__ if infl and infl.inflection_week else None

    # UI/publisher payload: deduped, capped complaint reviews.
    shown = _dedupe_for_ui(classified)
    shown_dicts = [c.to_dict() for c in shown]

    # ── Agent 5: Publisher (Senso) — only on a real spike ────────────────────
    cited_url = None
    if inflection and inflection.get("severity", 0) >= PUBLISH_MIN_SEVERITY:
        try:
            publish = publish_alert_stub if USE_STUB_PUBLISHER else publish_alert
            cited_url = publish(product, reformulation_date or "unknown", shown_dicts, inflection).get("cited_url")
            print(f"[orchestrator] published -> {cited_url}")
        except Exception as e:
            print(f"[orchestrator] Agent 5 failed: {e}")

    return {
        "product": product,
        "reformulation_date": reformulation_date,
        "reviews": shown_dicts,
        "buckets": buckets,
        "inflection": inflection,
        "cited_url": cited_url,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "clickhouse": "configured" if ch.configured() else "local-fallback",
        "publisher": "stub" if USE_STUB_PUBLISHER else "senso-live",
    }
