# Reformulation Sentinel

An autonomous multi-agent system that catches botched product reformulations weeks
before they show up in sales data, then publishes a sourced alert.

Give it a product name. The agent finds when the product was reformulated, watches
live public sentiment across the web, detects the moment complaints spike, and
publishes a cited report, early enough for a category manager to react in week two
instead of the quarterly review.

## How it works

An orchestrator runs five specialist agents over live web data:

1. **Date-Finder** (Tavily) finds when the product was reformulated, from a product name alone.
2. **Retrieval** (Tavily) searches and cleans complaint mentions across news and the web.
3. **Classifier** (Prometheux) rule-classifies each complaint by type, with a traceable reason.
4. **Aggregator/Detector** (ClickHouse) rolls complaints up by week and category and detects the spike.
5. **Publisher** (cited.md) publishes a sourced alert when an inflection is detected.

## Sponsor tools

- **Tavily** — live web retrieval. Source-biased searches find both the reformulation
  date and dated complaint coverage, and extract clean text from messy pages. This is
  what makes it a real web agent acting on live data, not a script over a static file.
- **Prometheux** — ontology and declarative rule classification. Resolves product variants
  and classifies each complaint with a literal rule trace back to the source text and date,
  so a judge can see exactly why a complaint was counted.
- **ClickHouse** — real-time aggregation. One `complaints` MergeTree table; the week×category
  rollup that powers the chart and the inflection detection (peak vs pre-reformulation
  baseline) both run as SQL, recomputed as new complaints stream in. Idempotent ingestion
  via `uniqExact(source_url)`.
- **cited.md** — publishes the action: a sourced report where each claim links to its source.

## Demo target (validated)

Reese's Peanut Butter Cups (Hershey), recipe change surfacing February 2026. See `TEAM.md`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # fill TAVILY_API_KEY, CLICKHOUSE_HOST, CLICKHOUSE_PASSWORD

# run the full pipeline (prints the /run contract JSON)
python -m agent.pipeline "Reese's Peanut Butter Cups"

# validate retrieval + dates for a product
python -m scripts.validate "Reese's Peanut Butter Cups" --reform-date 2026-02-17

# verify the ClickHouse layer
python -m scripts.clickhouse_check "Reese's Peanut Butter Cups" --reform-date 2026-02-17
```

UI:

```bash
cd ui
npm install
npm run dev        # http://localhost:3000
```

## Repo layout

```
agent/
  tavily_agent.py      Agents 1-2: Date-Finder + Retrieval (Tavily)
  classify.py          Agent 3 local stand-in (Prometheux drops in)
  clickhouse_store.py  Agent 4: ClickHouse aggregation + inflection
  aggregate.py         Agent 4 local fallback (no ClickHouse needed)
  pipeline.py          Orchestrator: runs the agents, returns the /run contract
  schemas.py           The frozen data contract shared across agents
scripts/
  validate.py          Data-validation harness (is the spike real?)
  clickhouse_check.py  ClickHouse health + aggregation check
ui/                    Next.js dashboard (React, shadcn/ui, Tailwind)
```
