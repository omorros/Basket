# Prometheux Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn raw product reviews into contract-valid `ClassifiedReview` rows with a human-readable rule-trace, using a Prometheux/Vadalog knowledge graph behind a swappable client.

**Architecture:** A thin Python adapter loads reviews + seed tables as facts, runs Vadalog rules (entity resolution + marker classification + a date-relative rule), and maps engine output plus provenance into the frozen contract. The engine sits behind a 4-method `PxClient` interface; a `MockPxClient` simulates the rule semantics in plain Python so the module is fully testable before the token or teammates exist. Swapping to the real `prometheux_chain` SDK touches one file.

**Tech Stack:** Python 3.9+ (3.13 recommended), pytest, `prometheux_chain` (real path only). Zero non-stdlib deps for the mock path.

## Global Constraints

- The data contract in `docs/superpowers/specs/2026-06-26-prometheux-classifier-design.md` is FROZEN. `Review` and `ClassifiedReview` keys and value domains must not change.
- `complaint_category` is exactly one of: `taste`, `texture`, `packaging`, `price`, `none`.
- Keep the Vadalog rule set to 5-8 rules (PRD risk register).
- All secrets via env var `PMTX_TOKEN`; never hard-code tokens.
- `rule_trace` must come from engine provenance (`@explain` / `@model`), not hand-written prose, on the real path. The mock mirrors the same trace shape.
- Prose/docs: no em dashes, en dashes, or decorative dashes (use commas, colons, parentheses).
- TDD throughout: failing test first, minimal code, green, commit.

---

### Task 1: Contract types and validator

**Files:**
- Create: `classifier/__init__.py`
- Create: `classifier/contract.py`
- Test: `classifier/tests/test_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Review` (TypedDict), `ClassifiedReview` (TypedDict), `VALID_CATEGORIES: set[str]`, `CLASSIFIED_KEYS: set[str]`, `validate_classified(row: dict) -> None` (raises `ValueError` on a bad row).

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_contract.py
import pytest
from classifier.contract import validate_classified, VALID_CATEGORIES

def _good_row():
    return {
        "url": "https://r/1", "variant_id": "coke-zero-2017",
        "complaint_category": "taste", "published_date": "2017-05-12",
        "rule_trace": ["matched alias", "taste marker"], "raw_excerpt": "tastes weird",
    }

def test_valid_row_passes():
    validate_classified(_good_row())  # no raise

def test_missing_key_raises():
    row = _good_row(); del row["variant_id"]
    with pytest.raises(ValueError):
        validate_classified(row)

def test_bad_category_raises():
    row = _good_row(); row["complaint_category"] = "smell"
    with pytest.raises(ValueError):
        validate_classified(row)

def test_categories_are_frozen():
    assert VALID_CATEGORIES == {"taste", "texture", "packaging", "price", "none"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_contract.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.contract'`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/__init__.py
```
```python
# classifier/contract.py
from typing import List, TypedDict

class Review(TypedDict):
    url: str
    source: str
    text: str
    published_date: str   # ISO 8601
    product_query: str

class ClassifiedReview(TypedDict):
    url: str
    variant_id: str
    complaint_category: str
    published_date: str
    rule_trace: List[str]
    raw_excerpt: str

VALID_CATEGORIES = {"taste", "texture", "packaging", "price", "none"}
CLASSIFIED_KEYS = {
    "url", "variant_id", "complaint_category",
    "published_date", "rule_trace", "raw_excerpt",
}

def validate_classified(row: dict) -> None:
    missing = CLASSIFIED_KEYS - row.keys()
    if missing:
        raise ValueError(f"ClassifiedReview missing keys: {sorted(missing)}")
    if row["complaint_category"] not in VALID_CATEGORIES:
        raise ValueError(f"bad complaint_category: {row['complaint_category']!r}")
    if not isinstance(row["rule_trace"], list):
        raise ValueError("rule_trace must be a list")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_contract.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add classifier/__init__.py classifier/contract.py classifier/tests/test_contract.py
git commit -m "feat(classifier): frozen contract types + validator"
```

---

### Task 2: Demo seed tables

**Files:**
- Create: `classifier/seeds.py`
- Test: `classifier/tests/test_seeds.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Seeds` (dataclass with `aliases: list[tuple[str,str]]`, `supersedes: list[tuple[str,str,str]]`, `markers: list[tuple[str,str]]`), `CATEGORY_PRECEDENCE: list[str]`, `DEMO_SEEDS: Seeds`. Swap `DEMO_SEEDS` once the demo product is chosen.

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_seeds.py
from classifier.seeds import DEMO_SEEDS, CATEGORY_PRECEDENCE
from classifier.contract import VALID_CATEGORIES

def test_aliases_point_to_a_known_variant():
    variants = {v for _, v in DEMO_SEEDS.aliases}
    superseding = {new for new, _, _ in DEMO_SEEDS.supersedes}
    assert variants & superseding, "at least one aliased variant must have a supersede edge"

def test_markers_use_valid_categories():
    for _, cat in DEMO_SEEDS.markers:
        assert cat in VALID_CATEGORIES

def test_precedence_covers_complaint_categories():
    assert set(CATEGORY_PRECEDENCE) == VALID_CATEGORIES - {"none"}

def test_supersedes_dates_are_iso():
    for _, _, d in DEMO_SEEDS.supersedes:
        assert len(d) == 10 and d[4] == "-" and d[7] == "-"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_seeds.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.seeds'`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/seeds.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class Seeds:
    aliases: List[Tuple[str, str]]          # (alias_string, variant_id)
    supersedes: List[Tuple[str, str, str]]  # (new_variant, old_variant, reform_date_iso)
    markers: List[Tuple[str, str]]          # (phrase, category)

CATEGORY_PRECEDENCE = ["taste", "texture", "packaging", "price"]

# Placeholder demo product. Replace with the chosen product's real aliases,
# documented reformulation date, and tuned markers before the demo.
DEMO_SEEDS = Seeds(
    aliases=[
        ("coke zero", "coke-zero-2017"),
        ("coca-cola zero sugar", "coke-zero-2017"),
        ("diet coke zero", "coke-zero-2017"),
        ("coca cola zero", "coke-zero-2017"),
    ],
    supersedes=[
        ("coke-zero-2017", "coke-zero-2016", "2017-04-01"),
    ],
    markers=[
        ("tastes like chemicals", "taste"),
        ("new recipe", "taste"),
        ("changed the recipe", "taste"),
        ("doesn't taste the same", "taste"),
        ("tastes different", "taste"),
        ("watery", "texture"),
        ("flat", "texture"),
        ("new can", "packaging"),
        ("new bottle", "packaging"),
        ("price went up", "price"),
        ("too expensive", "price"),
    ],
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_seeds.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add classifier/seeds.py classifier/tests/test_seeds.py
git commit -m "feat(classifier): demo seed tables (alias/supersedes/marker)"
```

---

### Task 3: PxClient interface + MockPxClient (rule semantics)

**Files:**
- Create: `classifier/px_client.py`
- Test: `classifier/tests/test_mock_px.py`

**Interfaces:**
- Consumes: `Seeds` from `classifier.seeds`, `CATEGORY_PRECEDENCE`.
- Produces: `PxClient` (Protocol) with `load(reviews: list[dict], seeds: Seeds, rules_text: str) -> None`, `run() -> None`, `fetch_classified() -> list[dict]` (rows with keys `url, variant_id, complaint_category, published_date, raw_excerpt`), `trace(url: str) -> list[str]`. Plus `MockPxClient` implementing it.

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_mock_px.py
from classifier.px_client import MockPxClient
from classifier.seeds import DEMO_SEEDS

def _client(reviews):
    c = MockPxClient()
    c.load(reviews, DEMO_SEEDS, rules_text="")
    c.run()
    return c

def test_resolves_alias_to_variant():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "tastes like chemicals now", "published_date": "2017-05-12",
                  "product_query": "Coke Zero"}])
    row = c.fetch_classified()[0]
    assert row["variant_id"] == "coke-zero-2017"

def test_post_reform_taste_classified_with_trace():
    c = _client([{"url": "u1", "source": "reddit",
                  "text": "this tastes like chemicals now", "published_date": "2017-05-12",
                  "product_query": "Coca-Cola Zero Sugar"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "taste"
    assert row["raw_excerpt"]
    trace = c.trace("u1")
    assert any("post-reformulation" in t for t in trace)

def test_neutral_review_is_none():
    c = _client([{"url": "u2", "source": "reddit",
                  "text": "love this drink, perfect", "published_date": "2018-01-01",
                  "product_query": "Coke Zero"}])
    row = c.fetch_classified()[0]
    assert row["complaint_category"] == "none"

def test_pre_reform_complaint_not_flagged_post():
    c = _client([{"url": "u3", "source": "reddit",
                  "text": "tastes different lately", "published_date": "2016-01-01",
                  "product_query": "Coke Zero"}])
    trace = c.trace("u3")
    assert not any("post-reformulation" in t for t in trace)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_mock_px.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.px_client'`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/px_client.py
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
                _, rd = reform[variant]
                trace.append(f'{variant} supersedes {reform[variant][0]}, reformulated {rd} (supersedes edge).')
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_mock_px.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add classifier/px_client.py classifier/tests/test_mock_px.py
git commit -m "feat(classifier): PxClient interface + MockPxClient rule semantics"
```

---

### Task 4: Vadalog rules program

**Files:**
- Create: `classifier/rules.vada`
- Test: `classifier/tests/test_rules_file.py`

**Interfaces:**
- Consumes: nothing (text asset loaded by the adapter and the real client).
- Produces: `classifier/rules.vada` containing the declarative program. The local test only asserts the program declares the required heads and annotations; semantic execution is verified on the real engine (Task 6).

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_rules_file.py
from pathlib import Path

RULES = Path("classifier/rules.vada").read_text()

def test_declares_required_predicates():
    for head in ["about(", "hit(", "post_reform(", "classified("]:
        assert head in RULES, f"missing rule head {head}"

def test_marks_output_and_explanation():
    assert '@output("classified")' in RULES
    assert "@explain(" in RULES
    assert "@model(" in RULES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_rules_file.py -v`
Expected: FAIL with `FileNotFoundError: classifier/rules.vada`

- [ ] **Step 3: Write minimal implementation**

```prolog
% classifier/rules.vada
% Reformulation Sentinel - classification rules (rules A-D).
% Facts (loaded by the adapter): review/5, alias/2, supersedes/3, marker/2.
% NOTE: built-in names for string-contains and date-compare are placeholders;
% confirm exact Vadalog syntax at the Prometheux sponsor booth.

% Rule A: entity resolution - resolve a review to a variant via an alias.
about(Url, V) :- review(Url, _, _, _, Query), alias(A, V), contains(Query, A).

% Rule B: marker hit - a review mentions a complaint category.
hit(Url, Cat, P) :- review(Url, _, Text, _, _), marker(P, Cat), contains(Text, P).

% Rule C: date-relative - taste/texture complaint dated after the reformulation.
post_reform(Url, Cat) :- about(Url, V), hit(Url, Cat, _),
                         supersedes(V, _, RD), review(Url, _, _, D, _), D >= RD.

% Rule D: classification head (the output predicate).
classified(Url, V, Cat, D, P) :- about(Url, V), hit(Url, Cat, P), review(Url, _, _, D, _).

@output("classified").

% Provenance + readable trace (the hero moment).
@explain("console").
@model("about", "['Url:string','V:string']", "review [Url] is about variant [V]").
@model("hit", "['Url:string','Cat:string','P:string']", "review [Url] mentions [Cat] via marker [P]").
@model("post_reform", "['Url:string','Cat:string']", "review [Url] is a post-reformulation [Cat] complaint").
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_rules_file.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add classifier/rules.vada classifier/tests/test_rules_file.py
git commit -m "feat(classifier): Vadalog rule program with @explain/@model"
```

---

### Task 5: Adapter (end-to-end against the contract)

**Files:**
- Create: `classifier/adapter.py`
- Create: `classifier/fixtures/reviews.json`
- Test: `classifier/tests/test_adapter.py`

**Interfaces:**
- Consumes: `MockPxClient`/`PxClient`, `DEMO_SEEDS`, `validate_classified`.
- Produces: `classify(reviews: list[dict], seeds: Seeds = DEMO_SEEDS, client: PxClient | None = None, rules_path: str = "classifier/rules.vada") -> list[dict]` returning contract-valid `ClassifiedReview` rows (each with a populated `rule_trace`).

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_adapter.py
import json
from pathlib import Path
from classifier.adapter import classify
from classifier.contract import validate_classified

FIX = json.loads(Path("classifier/fixtures/reviews.json").read_text())

def test_output_is_contract_valid():
    out = classify(FIX)
    assert len(out) == len(FIX)
    for row in out:
        validate_classified(row)
        assert row["rule_trace"], "rule_trace must be populated"

def test_known_post_reform_taste_row():
    out = {r["url"]: r for r in classify(FIX)}
    row = out["https://reddit.com/r/post1"]
    assert row["variant_id"] == "coke-zero-2017"
    assert row["complaint_category"] == "taste"
    assert any("post-reformulation" in t for t in row["rule_trace"])

def test_neutral_row_is_none():
    out = {r["url"]: r for r in classify(FIX)}
    assert out["https://reddit.com/r/neutral1"]["complaint_category"] == "none"
```

- [ ] **Step 2: Create the fixture (input data)**

```json
[
  {"url": "https://reddit.com/r/post1", "source": "reddit",
   "text": "Honestly this tastes like chemicals now, what happened?",
   "published_date": "2017-05-12", "product_query": "Coke Zero"},
  {"url": "https://reddit.com/r/post2", "source": "reddit",
   "text": "The new recipe is way too watery for me",
   "published_date": "2017-06-01", "product_query": "Coca-Cola Zero Sugar"},
  {"url": "https://reddit.com/r/neutral1", "source": "reddit",
   "text": "Still my favourite drink, never changes",
   "published_date": "2018-02-02", "product_query": "Coke Zero"},
  {"url": "https://reddit.com/r/pre1", "source": "reddit",
   "text": "tastes different lately, not sure why",
   "published_date": "2016-01-01", "product_query": "Coke Zero"}
]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_adapter.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.adapter'`

- [ ] **Step 4: Write minimal implementation**

```python
# classifier/adapter.py
from pathlib import Path
from typing import List, Optional
from classifier.contract import validate_classified
from classifier.px_client import PxClient, MockPxClient
from classifier.seeds import Seeds, DEMO_SEEDS

def classify(
    reviews: List[dict],
    seeds: Seeds = DEMO_SEEDS,
    client: Optional[PxClient] = None,
    rules_path: str = "classifier/rules.vada",
) -> List[dict]:
    client = client or MockPxClient()
    rules_text = Path(rules_path).read_text() if Path(rules_path).exists() else ""
    client.load(reviews, seeds, rules_text)
    client.run()
    out = []
    for row in client.fetch_classified():
        row = dict(row)
        row["rule_trace"] = client.trace(row["url"])
        validate_classified(row)
        out.append(row)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_adapter.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Run the whole suite**

Run: `cd ~/Desktop/Basket && python -m pytest classifier -v`
Expected: PASS (all tasks green)

- [ ] **Step 7: Commit**

```bash
git add classifier/adapter.py classifier/fixtures/reviews.json classifier/tests/test_adapter.py
git commit -m "feat(classifier): adapter wires mock engine to frozen contract"
```

---

### Task 6: RealPxClient swap (token-gated)

**Files:**
- Modify: `classifier/px_client.py` (append `RealPxClient`)
- Test: `classifier/tests/test_real_px.py`

**Interfaces:**
- Consumes: `prometheux_chain`, env `PMTX_TOKEN`, `classifier/rules.vada`.
- Produces: `RealPxClient` implementing the same `PxClient` interface. The integration test skips automatically when `PMTX_TOKEN` is unset.

- [ ] **Step 1: Write the (skippable) integration test**

```python
# classifier/tests/test_real_px.py
import os
import pytest
from classifier.adapter import classify

pytestmark = pytest.mark.skipif(
    not os.environ.get("PMTX_TOKEN"), reason="no PMTX_TOKEN; real engine not exercised"
)

def test_real_engine_matches_contract():
    from classifier.px_client import RealPxClient
    reviews = [{"url": "u1", "source": "reddit",
                "text": "this tastes like chemicals now", "published_date": "2017-05-12",
                "product_query": "Coke Zero"}]
    out = classify(reviews, client=RealPxClient())
    assert out[0]["variant_id"] == "coke-zero-2017"
    assert out[0]["rule_trace"]
```

- [ ] **Step 2: Run to verify it skips (no token yet)**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_real_px.py -v`
Expected: SKIPPED (1 skipped) - "no PMTX_TOKEN"

- [ ] **Step 3: Implement RealPxClient**

> Confirm the exact `prometheux_chain` fact-loading and explanation calls at the sponsor booth before relying on this. The flow below follows the documented SDK (`save_project` / `save_concept` / `run_concept` / `fetch_results`); the fact-loading and `explain` calls are the two spots to verify live.

```python
# append to classifier/px_client.py
import os
from typing import List
from classifier.seeds import Seeds, CATEGORY_PRECEDENCE  # already imported above; keep one import

class RealPxClient:
    """Real Prometheux engine via prometheux_chain. Same interface as MockPxClient."""

    def __init__(self, project_name: str = "reformulation_sentinel") -> None:
        import prometheux_chain as px
        self._px = px
        token = os.environ["PMTX_TOKEN"]
        px.config.set("PMTX_TOKEN", token)
        self._project = px.save_project(project_name=project_name)
        self._rows: List[dict] = []

    def _facts(self, reviews, seeds) -> str:
        # Vadalog facts prepended to the rule program.
        lines = []
        for r in reviews:
            t = r["text"].replace('"', "'")
            lines.append(f'review("{r["url"]}","{r["source"]}","{t}","{r["published_date"]}","{r["product_query"]}").')
        for a, v in seeds.aliases:
            lines.append(f'alias("{a}","{v}").')
        for new, old, rd in seeds.supersedes:
            lines.append(f'supersedes("{new}","{old}","{rd}").')
        for p, cat in seeds.markers:
            lines.append(f'marker("{p}","{cat}").')
        return "\n".join(lines)

    def load(self, reviews, seeds, rules_text="") -> None:
        program = self._facts(reviews, seeds) + "\n" + rules_text
        self._px.save_concept(project_id=self._project, definition=program)

    def run(self) -> None:
        self._px.run_concept(project_id=self._project, concept_name="classified")
        results = self._px.fetch_results(project_id=self._project, output_predicate="classified")
        # Map engine tuples (Url,V,Cat,D,P) to row dicts. VERIFY tuple order/shape live.
        self._rows = [
            {"url": t[0], "variant_id": t[1], "complaint_category": t[2],
             "published_date": t[3], "raw_excerpt": t[4]}
            for t in results
        ]

    def fetch_classified(self) -> List[dict]:
        return list(self._rows)

    def trace(self, url: str) -> List[str]:
        # @model annotations produce TextualExplanation sentences per derived fact.
        # VERIFY the explanation accessor at the booth; fall back to JsonExplanation walk.
        expl = self._px.fetch_results(project_id=self._project, output_predicate="classified")
        return [str(line) for line in []]  # placeholder until provenance accessor confirmed
```

- [ ] **Step 4: With a token, run the integration test**

Run: `cd ~/Desktop/Basket && PMTX_TOKEN=*** python -m pytest classifier/tests/test_real_px.py -v`
Expected (token present): PASS, or actionable failure pinpointing the fact-load / explain call to fix with the sponsor. The `trace` accessor is the known TODO to close live.

- [ ] **Step 5: Commit**

```bash
git add classifier/px_client.py classifier/tests/test_real_px.py
git commit -m "feat(classifier): RealPxClient SDK swap (token-gated integration test)"
```

---

### Task 7: Mock `/run` payload for the orchestrator/UI

**Files:**
- Create: `classifier/run_payload.py`
- Test: `classifier/tests/test_run_payload.py`

**Interfaces:**
- Consumes: `classify`, `classifier/fixtures/reviews.json`.
- Produces: `classified_payload(reviews: list[dict]) -> dict` returning `{"reviews": ClassifiedReview[]}` — the slice of the `/run` contract this module owns, so Agent 0/4 can integrate against a real shape immediately.

- [ ] **Step 1: Write the failing test**

```python
# classifier/tests/test_run_payload.py
import json
from pathlib import Path
from classifier.run_payload import classified_payload

FIX = json.loads(Path("classifier/fixtures/reviews.json").read_text())

def test_payload_shape():
    payload = classified_payload(FIX)
    assert set(payload) == {"reviews"}
    assert isinstance(payload["reviews"], list)
    assert payload["reviews"][0]["rule_trace"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_run_payload.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'classifier.run_payload'`

- [ ] **Step 3: Write minimal implementation**

```python
# classifier/run_payload.py
from typing import List
from classifier.adapter import classify

def classified_payload(reviews: List[dict]) -> dict:
    """The classifier's slice of the GET /run response (see TEAM.md)."""
    return {"reviews": classify(reviews)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Desktop/Basket && python -m pytest classifier/tests/test_run_payload.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Full suite + commit**

```bash
cd ~/Desktop/Basket && python -m pytest classifier -v
git add classifier/run_payload.py classifier/tests/test_run_payload.py
git commit -m "feat(classifier): /run payload slice for orchestrator integration"
```

---

## Self-Review

**Spec coverage:** entity resolution (Task 3 rule A, Task 4), marker classification (Task 3 rule B, Task 4), date-relative rule (Task 3 rule C, Task 4), rule-trace/provenance (Task 3 trace, Task 4 `@explain`/`@model`, Task 6 real accessor), frozen contract (Task 1, enforced in Task 5), seeds for demo product (Task 2), mock-now/real-later swap (Task 3 + Task 6), orchestrator integration (Task 7). All spec sections map to a task.

**Type consistency:** `PxClient` methods (`load`, `run`, `fetch_classified`, `trace`) are identical across `MockPxClient` (Task 3) and `RealPxClient` (Task 6) and are the only methods `classify` calls (Task 5). `Seeds` fields (`aliases`, `supersedes`, `markers`) are consistent across Tasks 2, 3, 6. `ClassifiedReview` keys match between `contract.py` (Task 1), the mock rows (Task 3), and `validate_classified` (Task 1, called in Task 5).

**Known TODOs (intentional, not placeholders):** the `RealPxClient.trace` provenance accessor and the fact-loading call are explicitly flagged to confirm at the sponsor booth; the integration test (Task 6) is the gate that closes them. Everything on the mock path is complete and runnable now.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-26-prometheux-classifier.md`. Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session with checkpoints for review.

Which approach?
