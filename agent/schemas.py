"""Shared data contract for the Reformulation Sentinel pipeline.

These are the frozen interfaces between agents (see TEAM.md). Every stage
produces/consumes these shapes so the three of us can build in parallel
against mocks. Do NOT change a field without telling the team.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Review:
    """Agent 2 (Retrieval, Tavily) -> Agent 3 (Classifier, Prometheux)."""

    url: str
    source: str                 # "reddit" | "amazon" | "tesco" | "forum" | "web"
    text: str                   # cleaned review/comment text
    published_date: Optional[str]  # ISO 8601 e.g. "2016-09-21", or None if unknown
    product_query: str          # the product name that was searched

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClassifiedReview:
    """Agent 3 (Classifier) -> Agent 4 (Aggregator, ClickHouse)."""

    url: str
    variant_id: str
    complaint_category: str     # "taste"|"texture"|"packaging"|"price"|"none"
    published_date: Optional[str]
    rule_trace: list[str] = field(default_factory=list)  # HERO MOMENT
    raw_excerpt: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WeeklyBucket:
    """Agent 4 (Aggregator) -> UI."""

    week: str                   # ISO week start, e.g. "2016-09-19"
    complaint_category: str
    count: int


@dataclass
class Inflection:
    """Agent 4 (Aggregator) -> UI."""

    inflection_week: str
    reformulation_date: str
    severity: float


@dataclass
class ReformulationDate:
    """Agent 1 (Date-Finder, Tavily) output."""

    product_query: str
    date: Optional[str]         # ISO 8601, or None if not found
    confidence: float           # 0..1
    evidence_url: Optional[str]
    evidence_quote: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
