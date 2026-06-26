"""Standalone health + verification for Agent 4 (ClickHouse).

Anyone on the team can run this to confirm ClickHouse is reachable, the table
exists, and the aggregation + inflection queries return sane data.

Run:
    python -m scripts.clickhouse_check                       # health + row counts
    python -m scripts.clickhouse_check "Reese's Peanut Butter Cups" --reform-date 2026-02-17
    python -m scripts.clickhouse_check "Reese's Peanut Butter Cups" --reset   # wipe that product first
"""

from __future__ import annotations

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv

from agent import clickhouse_store as ch

load_dotenv()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("product", nargs="?", help="optional: aggregate this product")
    ap.add_argument("--reform-date", help="YYYY-MM-DD for inflection detection")
    ap.add_argument("--reset", action="store_true", help="wipe this product's rows first")
    args = ap.parse_args()

    if not ch.configured():
        print("ClickHouse not configured. Set CLICKHOUSE_HOST + CLICKHOUSE_PASSWORD in .env.")
        return 1

    client = ch.get_client()
    print(f"Connected. server version {client.command('SELECT version()')}")
    ch.ensure_table(client)
    print(f"Table '{ch.TABLE}' ready.\n")

    print("Rows per product:")
    counts = ch.row_counts(client)
    if not counts:
        print("  (empty — run the pipeline once to ingest)")
    for pid, n in counts:
        print(f"  {n:>5}  {pid}")

    if args.product:
        pid = args.product.lower().strip()
        if args.reset:
            ch.reset_product(client, pid)
            print(f"\nReset rows for '{pid}'.")
        print(f"\nWeek x category for '{pid}':")
        for b in ch.weekly_buckets(client, pid):
            print(f"  {b.week}  {b.complaint_category:<10} {'#' * b.count} {b.count}")
        if args.reform_date:
            infl = ch.detect_inflection(client, pid, args.reform_date)
            print(f"\nInflection: peak week {infl.inflection_week}, "
                  f"severity {infl.severity}x (reformulation {infl.reformulation_date})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
