from typing import Dict, List, Protocol
from classifier.seeds import Seeds, CATEGORY_PRECEDENCE


class PxClient(Protocol):
    def load(self, reviews: List[dict], seeds: Seeds, rules_text: str) -> None: ...
    def run(self) -> None: ...
    def fetch_classified(self) -> List[dict]: ...
    def trace(self, url: str) -> List[str]: ...


def _excerpt(text: str, phrase: str) -> str:
    i = text.lower().find(phrase.lower())
    if i < 0:
        return ""
    start, end = max(0, i - 30), min(len(text), i + len(phrase) + 30)
    return ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")


class MockPxClient:
    """Simulates the Vadalog program (rules A-D) in plain Python.
    Mirrors the real engine's outputs: classified rows + per-url provenance."""

    def __init__(self) -> None:
        self._reviews: List[dict] = []
        self._seeds: Seeds = None  # type: ignore
        self._rows: List[dict] = []
        self._traces: Dict[str, List[str]] = {}

    def load(self, reviews, seeds, rules_text="") -> None:
        self._reviews, self._seeds = reviews, seeds

    def run(self) -> None:
        rows, traces = [], {}
        reform = {new: (old, rd) for new, old, rd in self._seeds.supersedes}
        for r in self._reviews:
            url, text, date = r["url"], r["text"], r["published_date"]
            query, tl = r["product_query"], r["text"].lower()
            trace: List[str] = []

            # Rule A: entity resolution
            variant = "unknown"
            for alias, v in self._seeds.aliases:
                if alias.lower() in query.lower() or alias.lower() in tl:
                    variant, used = v, alias
                    trace.append(f'Query "{query}" matches alias "{used}" -> variant {v} (rule A).')
                    break
            if variant == "unknown":
                trace.append(f'No alias matched query "{query}" -> variant unknown (rule A).')

            # Rule B: marker hits, choose one category by precedence
            hits = {cat: ph for ph, cat in self._seeds.markers if ph.lower() in tl}
            category, phrase = "none", ""
            for cat in CATEGORY_PRECEDENCE:
                if cat in hits:
                    category, phrase = cat, hits[cat]
                    trace.append(f'Text contains "{phrase}" -> {cat} marker (rule B).')
                    break

            # Rule C: date-relative
            if category in ("taste", "texture") and variant in reform:
                old, rd = reform[variant]
                trace.append(f'{variant} supersedes {old}, reformulated {rd} (supersedes edge).')
                if date >= rd:
                    trace.append(f'Review dated {date} >= reformulation {rd} -> post-reformulation {category} complaint (rule C).')

            if category == "none":
                trace.append("No complaint markers matched -> category none.")

            rows.append({
                "url": url, "variant_id": variant, "complaint_category": category,
                "published_date": date, "raw_excerpt": _excerpt(text, phrase),
            })
            traces[url] = trace
        self._rows, self._traces = rows, traces

    def fetch_classified(self) -> List[dict]:
        return list(self._rows)

    def trace(self, url: str) -> List[str]:
        return self._traces.get(url, [])
