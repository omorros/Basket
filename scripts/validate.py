"""Data-validation harness — the #1 pre-build check (PRD §6 / risk register).

Goal: BEFORE the team builds on it, confirm Tavily can actually pull dated
complaints about the chosen product and that a real time-clustered spike
exists around the reformulation date.

Run:
    python -m scripts.validate "Quest Bar"
    python -m scripts.validate "Quest Bar" --reform-date 2016-09-21

It prints:
  - Date-Finder's autonomous guess at the reformulation date
  - every retrieved review with its (best-effort) date + source + snippet
  - a month-by-month histogram of dated reviews so you can EYEBALL the spike
  - how many reviews carry a usable date (the key risk: undated Reddit results)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

# Windows consoles default to cp1252 and crash on emoji in review text.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv

from agent.tavily_agent import (
    retrieve_reviews,
    find_reformulation_date,
    enrich_reddit_dates,
)

load_dotenv()  # read TAVILY_API_KEY from .env


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("product", help='e.g. "Quest Bar"')
    ap.add_argument("--reform-date", help="known date YYYY-MM-DD to sanity-check against")
    ap.add_argument("--max", type=int, default=15, help="max results per source")
    ap.add_argument(
        "--sources", default="news,web", help="comma list: news,web,reddit,amazon"
    )
    args = ap.parse_args()
    sources = tuple(s.strip() for s in args.sources.split(",") if s.strip())

    print(f"\n=== DATE-FINDER (Agent 1) — {args.product} ===")
    rd = find_reformulation_date(args.product)
    if rd.date:
        print(f"  found: {rd.date}  (confidence {rd.confidence:.2f})")
        print(f"  source: {rd.evidence_url}")
        print(f"  quote:  {rd.evidence_quote[:160]}...")
    else:
        print("  no date found autonomously (fall back to the constant in the demo)")
    if args.reform_date:
        print(f"  known/expected date: {args.reform_date}")

    print(f"\n=== RETRIEVAL (Agent 2) — sources={sources} ===")
    reviews = retrieve_reviews(args.product, sources=sources, max_results=args.max)
    print(f"  {len(reviews)} reviews retrieved; enriching Reddit dates...")
    enrich_reddit_dates(reviews)
    print()

    dated = 0
    months: Counter[str] = Counter()
    for rv in reviews:
        flag = rv.published_date or "????-??"
        if rv.published_date:
            dated += 1
            months[rv.published_date[:7]] += 1
        print(f"  [{flag}] ({rv.source}) {rv.url}")
        print(f"      {rv.text[:140].replace(chr(10), ' ')}...")

    print("\n=== SPIKE CHECK (dated reviews by month) ===")
    if not months:
        print("  ⚠️  NO usable dates — Tavily search isn't returning dated results.")
        print("      Mitigation: enrich via client.extract() + regex, or switch source.")
    else:
        for ym in sorted(months):
            bar = "█" * months[ym]
            print(f"  {ym}  {bar} {months[ym]}")

    print(f"\n=== VERDICT ===")
    print(f"  dated/total: {dated}/{len(reviews)}")
    if args.reform_date and months:
        near = [ym for ym in months if ym >= args.reform_date[:7]]
        print(f"  reviews at/after reform month {args.reform_date[:7]}: "
              f"{sum(months[m] for m in near)}")
    print("  → Decide: is there a visible cluster near the reformulation date? "
          "If yes, GREEN-LIGHT this product.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
