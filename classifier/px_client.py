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


def _vada_str(s: str) -> str:
    """Escape a Python string for inlining as a Vadalog string literal."""
    return (s or "").replace("\\", "\\\\").replace('"', "'").replace("\n", " ").strip()


def _facts(reviews: List[dict], seeds: Seeds) -> str:
    """Serialize reviews + seed tables as inline Vadalog facts."""
    lines: List[str] = []
    for r in reviews:
        lines.append(
            f'review("{_vada_str(r["url"])}","{_vada_str(r.get("source",""))}",'
            f'"{_vada_str(r["text"])}","{_vada_str(r.get("published_date") or "")}",'
            f'"{_vada_str(r["product_query"])}").'
        )
    for a, v in seeds.aliases:
        lines.append(f'alias("{_vada_str(a)}","{_vada_str(v)}").')
    for new, old, rd in seeds.supersedes:
        lines.append(f'supersedes("{_vada_str(new)}","{_vada_str(old)}","{rd}").')
    for p, cat in seeds.markers:
        lines.append(f'marker("{_vada_str(p)}","{cat}").')
    return "\n".join(lines)


def _rows_from_results(results: object) -> List[list]:
    """Normalize prometheux_chain.fetch_results output into a list of column-lists.

    Confirmed live shape (SDK 0.2.14):
      {'predicate': ..., 'results': {'facts': [[...], ...], 'columnNames': [...]},
       'pagination': {'has_next': bool, ...}}
    Falls back gracefully if a future version returns a bare list.
    """
    facts: object = []
    if isinstance(results, dict):
        inner = results.get("results")
        if isinstance(inner, dict):
            facts = inner.get("facts", [])
        else:
            facts = results.get("facts") or results.get("data") or results.get("rows") or []
    elif isinstance(results, (list, tuple)):
        facts = results
    else:
        facts = getattr(results, "facts", None) or []
    out: List[list] = []
    for row in facts or []:
        if isinstance(row, dict):
            out.append(list(row.values()))
        elif isinstance(row, (list, tuple)):
            out.append(list(row))
        else:
            out.append([row])
    return out


def _has_next(results: object) -> bool:
    if isinstance(results, dict):
        return bool(results.get("pagination", {}).get("has_next"))
    return False


class RealPxClient:
    """Real Prometheux engine via prometheux_chain. Same interface as MockPxClient.

    The engine does the reasoning (entity resolution, marker classification, the
    date-relative join). The trace is then formatted in Python from the engine's
    `classified` output so the row shape is identical to the mock.
    """

    def __init__(self, project_name: str = "reformulation_sentinel") -> None:
        import os
        import prometheux_chain as px
        self._px = px
        token = os.environ.get("PMTX_TOKEN", "").strip()
        if not token:
            raise RuntimeError("PMTX_TOKEN not set (load it from .env)")
        os.environ["PMTX_TOKEN"] = token
        url = os.environ.get("JARVISPY_URL", "").strip()
        if url and "{" not in url:
            px.config.set("JARVISPY_URL", url)
        self._project = px.save_project(project_name=project_name)
        self._reviews: List[dict] = []
        self._seeds: Seeds = None  # type: ignore
        self._rows: List[dict] = []
        self._traces: Dict[str, List[str]] = {}

    def load(self, reviews, seeds, rules_text="") -> None:
        self._reviews, self._seeds = reviews, seeds
        definition = _facts(reviews, seeds) + "\n" + (rules_text or "")
        self._px.save_concept(
            project_id=self._project, definition=definition, concept_name="classified",
            output_predicate="classified",
        )

    @staticmethod
    def _retry(fn, tries: int = 12, delay: float = 8.0):
        """The engine runs one job at a time; back off and retry while it is busy."""
        import time
        last = None
        for _ in range(tries):
            try:
                return fn()
            except Exception as e:  # noqa: BLE001
                last = e
                if "ENGINE_BUSY" in str(e) or "busy" in str(e).lower():
                    time.sleep(delay)
                    continue
                raise
        raise last  # type: ignore[misc]

    def _fetch_all(self, predicate: str) -> List[list]:
        rows, page, size = [], 1, 200
        while True:
            res = self._retry(lambda: self._px.fetch_results(
                project_id=self._project, output_predicate=predicate,
                page=page, page_size=size,
            ))
            rows.extend(_rows_from_results(res))
            if not _has_next(res):
                break
            page += 1
        return rows

    def run(self) -> None:
        self._retry(lambda: self._px.run_concept(
            project_id=self._project, concept_name="classified", persist_outputs=True,
        ))
        # engine output rows: [Url, Variant, Category, Phrase, Date, ReformDate, Phase]
        engine = self._fetch_all("classified")
        by_url: Dict[str, List[list]] = {}
        for row in engine:
            if len(row) >= 7:
                by_url.setdefault(str(row[0]), []).append(row)

        reform = {new: (old, rd) for new, old, rd in self._seeds.supersedes}
        rows, traces = [], {}
        for r in self._reviews:
            url, text, query = r["url"], r["text"], r["product_query"]
            date = r.get("published_date") or ""
            trace: List[str] = []
            matched_alias = next(
                (a for a, _ in self._seeds.aliases if a.lower() in query.lower()), None
            )

            hits = by_url.get(url, [])
            if hits:
                # pick one category by precedence; keep that row's columns
                chosen = min(
                    hits,
                    key=lambda h: CATEGORY_PRECEDENCE.index(str(h[2]))
                    if str(h[2]) in CATEGORY_PRECEDENCE else 99,
                )
                _, variant, category, phrase, d, rd, phase = (
                    chosen[0], str(chosen[1]), str(chosen[2]), str(chosen[3]),
                    str(chosen[4]), str(chosen[5]), str(chosen[6]),
                )
                if matched_alias:
                    trace.append(f'Query "{query}" matches alias "{matched_alias}" -> variant {variant} (rule A).')
                else:
                    trace.append(f'Resolved to variant {variant} (rule A).')
                trace.append(f'Text contains "{phrase}" -> {category} marker (rule B).')
                old = reform.get(variant, ("", rd))[0]
                trace.append(f'{variant} supersedes {old}, reformulated {rd} (supersedes edge).')
                if phase == "post":
                    trace.append(f'Review dated {d} >= reformulation {rd} -> post-reformulation {category} complaint (rule C).')
                rows.append({
                    "url": url, "variant_id": variant, "complaint_category": category,
                    "published_date": date, "raw_excerpt": _excerpt(text, phrase),
                })
            else:
                variant = (
                    next((v for a, v in self._seeds.aliases if a.lower() in query.lower()), "unknown")
                )
                if matched_alias:
                    trace.append(f'Query "{query}" matches alias "{matched_alias}" -> variant {variant} (rule A).')
                else:
                    trace.append(f'No alias matched query "{query}" -> variant unknown (rule A).')
                trace.append("No complaint markers matched -> category none.")
                rows.append({
                    "url": url, "variant_id": variant, "complaint_category": "none",
                    "published_date": date, "raw_excerpt": "",
                })
            traces[url] = trace
        self._rows, self._traces = rows, traces

    def fetch_classified(self) -> List[dict]:
        return list(self._rows)

    def trace(self, url: str) -> List[str]:
        return self._traces.get(url, [])
