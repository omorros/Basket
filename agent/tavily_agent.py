"""Tavily-backed agents: Date-Finder (Agent 1) and Retrieval (Agent 2).

Both are owned by the UI/Tavily teammate. They emit the frozen contract
shapes from schemas.py so the Classifier downstream needs no glue.

Tavily SDK reference (tavily-python):
    client.search(query, search_depth=, topic=, include_domains=,
                  max_results=, time_range=, days=) -> {"results": [...]}
    each result: {"title","url","content","score","published_date"?}
    client.extract(urls) -> {"results":[{"url","raw_content"}], ...}
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from tavily import TavilyClient

from .schemas import Review, ReformulationDate


# ---- date parsing helpers ---------------------------------------------------

_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        ["", "January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"],
    )
    if m
}
# e.g. "September 21, 2016" or "Sep 2016" or "21 September 2016"
_LONG_RE = re.compile(
    r"\b(?:(\d{1,2})\s+)?([A-Za-z]{3,9})\.?\s+(?:(\d{1,2}),?\s+)?(\d{4})\b"
)


def _norm_month(name: str) -> Optional[int]:
    name = name.lower()
    for full, idx in _MONTHS.items():
        if full.lower().startswith(name) or name.startswith(full.lower()[:3]):
            return idx
    return None


def parse_date(text: Optional[str]) -> Optional[str]:
    """Best-effort extract an ISO date from a string. Returns YYYY-MM-DD or None."""
    if not text:
        return None
    m = _ISO_RE.search(text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = _LONG_RE.search(text)
    if m:
        d1, mon, d2, year = m.groups()
        mi = _norm_month(mon)
        if mi:
            day = d1 or d2 or "01"
            return f"{int(year):04d}-{mi:02d}-{int(day):02d}"
    return None


# ---- client -----------------------------------------------------------------

def _client(api_key: Optional[str] = None) -> TavilyClient:
    key = api_key or os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError(
            "TAVILY_API_KEY not set. Put it in a .env file (see .env.example) "
            "or export it in your shell."
        )
    return TavilyClient(api_key=key)


# Retrieval strategy per source. "news" is the workhorse: Tavily returns a
# reliable published_date for news, which is what powers the spike chart.
# Reddit search returns good snippets but no fetchable dates (blocked), so it
# is supplementary-quote-only.
SOURCE_CONFIG = {
    "news":   {"topic": "news", "domains": None},
    "web":    {"topic": "general", "domains": None},
    "reddit": {"topic": "general", "domains": ["reddit.com"]},
    "amazon": {"topic": "general", "domains": ["amazon.com", "amazon.co.uk"]},
}

COMPLAINT_TERMS = (
    "recipe change OR reformulated OR \"changed the recipe\" OR "
    "\"bring back the old\" OR tastes different OR texture OR backlash"
)


def _to_iso(published: Optional[str]) -> Optional[str]:
    """Tavily news dates look like 'Fri, 03 Apr 2026 ...' — normalise to ISO."""
    return parse_date(published) if published else None


# ---- Agent 2: Retrieval -----------------------------------------------------

def retrieve_reviews(
    product: str,
    sources: tuple[str, ...] = ("news", "web"),
    max_results: int = 15,
    days: int = 180,
    api_key: Optional[str] = None,
) -> list[Review]:
    """Run source-biased searches for complaints about `product`.

    Returns Review[] (the contract shape). published_date comes from Tavily's
    own field (reliable for news) and falls back to parsing the text.
    `days` bounds news recency — we target LIVE reformulations.
    """
    client = _client(api_key)
    out: list[Review] = []
    seen_urls: set[str] = set()

    for source in sources:
        cfg = SOURCE_CONFIG.get(source, {"topic": "general", "domains": None})
        kwargs = dict(
            query=f"{product} {COMPLAINT_TERMS}",
            search_depth="advanced",
            max_results=max_results,
            topic=cfg["topic"],
            include_domains=cfg["domains"],
        )
        if cfg["topic"] == "news":
            kwargs["days"] = days
        resp = client.search(**kwargs)
        for r in resp.get("results", []):
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            published = _to_iso(r.get("published_date")) or parse_date(
                r.get("title", "") + " " + r.get("content", "")
            )
            out.append(
                Review(
                    url=url,
                    source=source,
                    text=(r.get("content") or "").strip(),
                    published_date=published,
                    product_query=product,
                )
            )
    return out


# ---- date enrichment (Tavily doesn't return dates for Reddit) ---------------

_REDDIT_RE = re.compile(r"reddit\.com/r/[^/]+/comments/([a-z0-9]+)", re.I)
_UA = "Mozilla/5.0 (ReformulationSentinel/0.1 research bot)"


def enrich_reddit_dates(reviews: list[Review]) -> list[Review]:
    """Fill published_date for Reddit reviews by querying the thread's JSON.

    Reddit exposes <thread-url>.json with the post's created_utc. This is the
    fallback for the known risk that Tavily search omits Reddit dates.
    Failures are silent (date stays None) so one bad URL can't break the run.
    """
    for rv in reviews:
        if rv.published_date or "reddit.com" not in rv.url:
            continue
        m = _REDDIT_RE.search(rv.url)
        if not m:
            continue
        try:
            url = rv.url.split("?")[0].rstrip("/") + ".json"
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            created = data[0]["data"]["children"][0]["data"]["created_utc"]
            rv.published_date = (
                datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat()
            )
        except Exception:
            pass  # leave date as None
    return reviews


# ---- Agent 1: Date-Finder ---------------------------------------------------

# Reformulations we care about are recent — ignore founding/heritage dates.
_MIN_REFORM_DATE = "2023-01-01"


def find_reformulation_date(
    product: str,
    api_key: Optional[str] = None,
    days: int = 270,
) -> ReformulationDate:
    """Autonomously find WHEN `product` was reformulated.

    Strategy: dated news in a recency window; the EARLIEST credible coverage
    date is the proxy for when the reformulation surfaced. Recency-bounded so
    we never grab a brand's founding year. This is the autonomy story (PRD §6).
    """
    client = _client(api_key)
    # Pool several angles so the EARLIEST (breaking) coverage isn't crowded out
    # by the much-heavier later coverage (e.g. a reversal).
    angles = [
        f"{product} recipe change backlash",
        f"{product} accuses changing recipe complaints",
        f"{product} tastes different reformulation",
    ]
    best: Optional[ReformulationDate] = None
    for q in angles:
        resp = client.search(
            query=q, topic="news", search_depth="advanced", max_results=12, days=days
        )
        for r in resp.get("results", []):
            d = parse_date(r.get("published_date"))
            if not d or d < _MIN_REFORM_DATE:
                continue
            cand = ReformulationDate(
                product_query=product,
                date=d,
                confidence=min(0.9, float(r.get("score", 0.5)) + 0.3),
                evidence_url=r.get("url"),
                evidence_quote=f"{r.get('title','')}".strip()[:280],
            )
            # earliest coverage in-window ≈ when the reformulation broke
            if best is None or (cand.date or "9999") < (best.date or "9999"):
                best = cand
    if best is None:
        return ReformulationDate(
            product_query=product, date=None, confidence=0.0, evidence_url=None
        )
    return best
