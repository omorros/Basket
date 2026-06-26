"""Agent 4 — ClickHouse Aggregator/Detector (the real sponsor tool).

Stores classified complaints in one MergeTree table and answers two questions
fast, even as rows keep streaming in:
  1. Aggregate: complaint volume by week x category  -> WeeklyBucket[]
  2. Detect:    the spike week vs the pre-reformulation baseline -> Inflection

Output shapes are the frozen contract (schemas.py), so this is a drop-in
replacement for the local stand-in in aggregate.py. Re-runs are idempotent:
counts use uniqExact(source_url), so inserting the same review twice never
double-counts.

Env (put in .env):
  CLICKHOUSE_HOST      e.g. abc123.europe-west4.gcp.clickhouse.cloud
  CLICKHOUSE_PASSWORD  the 'default' user password from ClickHouse Cloud
  CLICKHOUSE_PORT      optional, defaults to 8443 (https)
  CLICKHOUSE_USER      optional, defaults to "default"
  CLICKHOUSE_DATABASE  optional, defaults to "default"
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import clickhouse_connect

from .schemas import ClassifiedReview, WeeklyBucket, Inflection

TABLE = "complaints"

_COLS = ["ts", "product_id", "variant_id", "complaint_category", "source_url", "raw_excerpt"]


def configured() -> bool:
    """True if ClickHouse creds are present; lets the pipeline fall back gracefully."""
    return bool(os.environ.get("CLICKHOUSE_HOST") and os.environ.get("CLICKHOUSE_PASSWORD"))


def get_client():
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=os.environ.get("CLICKHOUSE_DATABASE", "default"),
        secure=True,
    )


def ensure_table(client) -> None:
    client.command(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            ts                  DateTime,
            product_id          String,
            variant_id          String,
            complaint_category  LowCardinality(String),
            source_url          String,
            raw_excerpt         String
        ) ENGINE = MergeTree()
        ORDER BY (product_id, ts)
        """
    )


def insert_reviews(client, product_id: str, reviews: list[ClassifiedReview]) -> int:
    rows = []
    for r in reviews:
        if not r.published_date:
            continue
        rows.append([
            datetime.fromisoformat(r.published_date),
            product_id,
            r.variant_id or "",
            r.complaint_category or "none",
            r.url,
            (r.raw_excerpt or "")[:500],
        ])
    if rows:
        client.insert(TABLE, rows, column_names=_COLS)
    return len(rows)


def reset_product(client, product_id: str) -> None:
    """Delete a product's rows for a clean demo re-seed (lightweight DELETE)."""
    client.command(
        f"DELETE FROM {TABLE} WHERE product_id = {{pid:String}}",
        parameters={"pid": product_id},
    )


def row_counts(client) -> list[tuple[str, int]]:
    """(product_id, row count) for every product in the table. Health/demo aid."""
    res = client.query(
        f"SELECT product_id, count() AS n FROM {TABLE} GROUP BY product_id ORDER BY n DESC"
    )
    return [(r[0], int(r[1])) for r in res.result_rows]


def weekly_buckets(client, product_id: str) -> list[WeeklyBucket]:
    """Complaint volume by week x category (the chart query)."""
    res = client.query(
        f"""
        SELECT toString(toMonday(ts)) AS week,
               complaint_category,
               uniqExact(source_url)  AS cnt
        FROM {TABLE}
        WHERE product_id = {{pid:String}} AND complaint_category != 'none'
        GROUP BY week, complaint_category
        ORDER BY week, complaint_category
        """,
        parameters={"pid": product_id},
    )
    return [
        WeeklyBucket(week=row[0], complaint_category=row[1], count=int(row[2]))
        for row in res.result_rows
    ]


def detect_inflection(client, product_id: str, reformulation_date: Optional[str]) -> Inflection:
    """Heaviest complaint week at/after the reformulation vs the pre-baseline.

    ClickHouse does the heavy lift: weekly rollup, then peak and baseline in one
    pass. Severity (peak / baseline) is the final divide.
    """
    if not reformulation_date:
        return Inflection(inflection_week="", reformulation_date="", severity=0.0)

    res = client.query(
        f"""
        WITH weekly AS (
            SELECT toMonday(ts) AS w, uniqExact(source_url) AS c
            FROM {TABLE}
            WHERE product_id = {{pid:String}} AND complaint_category != 'none'
            GROUP BY w
        ),
        ref AS (SELECT toMonday(toDate({{ref:String}})) AS rw)
        SELECT
            (SELECT toString(argMax(w, c)) FROM weekly WHERE w >= (SELECT rw FROM ref)) AS peak_week,
            (SELECT max(c)                 FROM weekly WHERE w >= (SELECT rw FROM ref)) AS peak,
            (SELECT avg(c)                 FROM weekly WHERE w <  (SELECT rw FROM ref)) AS baseline
        """,
        parameters={"pid": product_id, "ref": reformulation_date},
    )
    peak_week, peak, baseline = res.result_rows[0]

    def _num(x: object) -> float:
        try:
            v = float(x)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return 0.0 if v != v else v  # NaN guard (no pre-reform rows -> null avg)

    peak = _num(peak)
    baseline = _num(baseline)
    # No pre-reform baseline means complaints rose from ~zero. Floor the baseline
    # at 1 complaint/week so severity reads as the peak week's height (what the
    # chart shows) rather than a NaN or an inflated multiple.
    severity = round(peak / max(baseline, 1.0), 2)
    return Inflection(
        inflection_week=peak_week or "",
        reformulation_date=reformulation_date,
        severity=severity,
    )


def aggregate_and_detect(
    product_id: str,
    reviews: list[ClassifiedReview],
    reformulation_date: Optional[str],
) -> tuple[list[WeeklyBucket], Inflection]:
    """One call the orchestrator uses: store rows, then aggregate + detect."""
    client = get_client()
    ensure_table(client)
    insert_reviews(client, product_id, reviews)
    return weekly_buckets(client, product_id), detect_inflection(client, product_id, reformulation_date)
