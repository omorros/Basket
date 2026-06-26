# TEAM — Reformulation Sentinel

Multi-agent system: an **Orchestrator** drives 5 specialist agents that turn a product name
into a published, sourced complaint-spike alert. See `PRD (1).md` for the pitch & demo script.

## DEMO TARGET (validated ✅) — Hershey / Reese's recipe change

We pivoted from Quest (2016) to a **live 2026** reformulation. Why: Reddit blocks both
`.json` and Tavily `extract`, so historical Reddit spikes can't be dated. Live news dates
cleanly via Tavily AND scores higher on "acts on real-time data".

- **Product:** Reese's Peanut Butter Cups (Hershey)
- **Change:** milk chocolate → cheaper compound coating on several Reese's variants
- **Timeline:** accusation breaks ~**Feb 17 2026** (inventor's grandson) → backlash builds →
  Hershey U-turns to classic recipe ~**Apr 1 2026**
- **Validation:** `python -m scripts.validate "Reese's Peanut Butter Cups" --reform-date 2026-02-17`
  → 17/30 dated, spike Feb (6) → Apr peak (11). Real grievance text, not neutral reporting.
- **Prometheux rules now target:** "tastes different/waxy", "changed the recipe", "compound
  coating vs real chocolate", complaints dated at/after the Feb change. (Teammate C.)

## Agents (6 total)

| # | Agent | Job | Tool | Owner |
|---|-------|-----|------|-------|
| 1 | Date-Finder | From product name, find *if/when* it was reformulated | Tavily | You |
| 2 | Retrieval | Query + fetch + clean reviews (Reddit/retailer/forums) | Tavily | You |
| 3 | Classifier | Entity-resolve variants + rule-classify w/ trace | Prometheux | C |
| 4 | Aggregator/Detector | Bucket volume by week×category, detect inflection | ClickHouse | C |
| 5 | Publisher | On inflection, emit sourced report → public URL | cited.md | B |
| 0 | Orchestrator | Run the loop, pass data agent→agent, fire Publisher | — | B |

## Ownership

- **You** — Date-Finder + Retrieval (Tavily) · data validation · UI (Next.js dashboard)
- **B** — Orchestrator (`/run?product=`) · cited.md Publisher
- **C** — Prometheux Classifier · ClickHouse Aggregator/Detector

## THE DATA CONTRACT (freeze this — everyone builds against it with mocks)

```python
# Agent 2 (Retrieval) -> Agent 3 (Classifier)
Review = {
  "url": str,            # source review/thread URL
  "source": str,         # "reddit" | "amazon" | "tesco" | "forum" | "web"
  "text": str,           # cleaned review/comment text
  "published_date": str, # ISO 8601, e.g. "2016-11-08"
  "product_query": str,  # the product name that was searched
}

# Agent 3 (Classifier) -> Agent 4 (Aggregator)
ClassifiedReview = {
  "url": str,
  "variant_id": str,            # resolved variant (handles aliases)
  "complaint_category": str,    # "taste" | "texture" | "packaging" | "price" | "none"
  "published_date": str,        # ISO 8601
  "rule_trace": list[str],      # which rules fired + why (HERO MOMENT)
  "raw_excerpt": str,           # the snippet that triggered the rule
}

# Agent 4 (Aggregator) -> UI
WeeklyBucket = { "week": str, "complaint_category": str, "count": int }   # week = ISO week start
Inflection   = { "inflection_week": str, "reformulation_date": str, "severity": float }
```

## API the UI calls (Orchestrator owns)

```
GET /run?product=<name>
-> { "reformulation_date": str,
     "reviews": ClassifiedReview[],
     "buckets": WeeklyBucket[],
     "inflection": Inflection,
     "cited_url": str }
```

UI builds against a mock `/run` returning this shape until the real pipeline lands.

## First 30 minutes

- [x] **You** — demo product picked + spike validated (Hershey/Reese's, see above)
- [ ] **B** — confirm the **cited.md API** at the sponsor booth (top open risk); stub Publisher to return a placeholder URL meanwhile
- [ ] **C** — confirm how to author + run Prometheux rules; sketch the ontology
- [ ] **All** — agree the contract above is frozen; commit `TEAM.md`

## Scope (from PRD §5)

- MUST: Tavily fetch (1 product, 1–2 sources) · Prometheux 5–8 rules + variant resolution + trace ·
  ClickHouse table + week×category query · chart w/ reformulation date marked · cited.md publish
- SHOULD: Date-Finder autonomy (first thing to cut if short on time)
- WON'T: multi-product · x402 billing · ontology UI · auth · broad source coverage

## Stack

Python (agents + FastAPI orchestrator) · Next.js/React (UI) · all sponsor keys in hand.
