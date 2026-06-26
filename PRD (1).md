# PRD — Reformulation Sentinel

*An autonomous web agent that catches botched product reformulations weeks before they show up in sales data — and publishes a sourced alert.*

**Status:** Hackathon build · **Time budget:** ~5 hrs to 4:30pm deadline
**Team size:** ≤3 · **Sponsors targeted:** Tavily · Prometheux · ClickHouse (+ cited.md publish)

---

## 1. The problem (the pitch, one breath)

Brands find out a recipe/packaging change backfired weeks or months too late — after sales dip and someone runs a root-cause analysis. The complaints ("bring back the old recipe", "tastes like chemicals now") are already public the day it happens, scattered across Reddit, retailer reviews, and forums. Nobody continuously watches that feed and ties it back to *when* the recipe changed.

**Reformulation Sentinel** closes the loop: give it a product name, and it autonomously finds out *if and when* the product was reformulated, watches live public sentiment, detects the inflection point, and **publishes a cited alert** — early enough for a category manager to react in week 2 instead of the quarterly review.

---

## 2. Why this wins (criteria → design)

The prize money is mostly **per-sponsor pools**, not one grand prize. Strategy: lean hardest on **Prometheux** (largest pool, and our CPG angle maps onto its "Biggest Business Impact" sub-prize), with ClickHouse and Tavily as strong secondary shots.

| Criterion | How we hit it |
|---|---|
| **Idea / real-world value** | Recognizable CPG/retail pain, explainable in one sentence to a non-technical judge. Quantified: catch it in week 2, not the quarterly review. |
| **Autonomy** | Input is *just a product name*. The agent finds the reformulation date itself (no magic constant), formulates its own queries, fetches, classifies, and publishes — one unbroken pipeline, run live. |
| **Tool Use (3+)** | Each tool does undeniable, visible work — see §4. Not token API calls. |
| **Technical Implementation** | Narrow, reliable slice that runs flawlessly live > broad and fragile. |
| **Presentation (3 min)** | Scripted, with the **Prometheux rule-trace** as the hero moment, not the chart. |

**The "act on the web" fix.** The challenge slide demands the agent *take real action — publish, monitor, orchestrate*, grounded in real sources, and **publish output to cited.md**. A dashboard alone reads as "observe, not act." So the agent doesn't just chart — on detecting an inflection it **auto-publishes a sourced report to cited.md**, each complaint claim linked to the real review URL. This converts "observe" into "publish, grounded in real sources" almost verbatim from the slide, and gives the demo a permanent public artifact as its payoff.

> **Monetization:** weakest fit, do NOT build under time pressure. One line in the pitch — "brands subscribe per-product; alerts billed via x402" — earns the nod without code.

---

## 3. End-to-end workflow

```
product name
   └─► [Tavily] find reformulation date  ──┐
   └─► [Tavily] fetch reviews/mentions      │ autonomous, no hand-curation
        across Reddit / retailer / forums   │
              │                              │
              ▼                              ▼
        [Prometheux] entity-resolve variants + classify each
        review via declarative rules → structured + traceable
              │
              ▼
        [ClickHouse] store rows, aggregate complaint volume
        per week × category
              │
              ▼
        detect inflection vs reformulation date
              │
              ▼
        [cited.md] publish sourced alert (each claim → review URL)
              │
              ▼
        dashboard: complaint volume over time, reformulation date marked
```

---

## 4. Tool responsibilities (and why not X)

**Tavily — live web retrieval.** Given a product name, runs source-biased searches (`site:reddit.com`, retailer review pages, general web) for reviews + the reformulation date itself, and extracts clean readable text from messy pages.
*Why not a generic scraper:* value is multi-source synthesis built for agents, not raw HTML. *This is what makes it a real web agent, not a toy on a static CSV.*

**Prometheux — ontology + rule-based classification (THE HERO).** Defines entities (Product, Variant, Review, ComplaintType, Category), relationships (`Variant --supersedes--> Variant` carries the reformulation date as a graph edge; `Review --mentions--> ComplaintType`), and **declarative rules** like *"if review text has taste-change markers AND is dated after the variant's supersede-date → PostReformulationTasteComplaint."*
*Why not an LLM classifier:* (1) **entity resolution** — "Coke Zero" / "Coca-Cola Zero Sugar" / "Diet Coke (Zero)" are one variant; string-matching fails. (2) **Explainability** — a judge asks "why was this counted as a reformulation complaint?" and gets a literal rule-trace back to source text + date, not "the LLM said so." This trace is the demo's hero moment.

**ClickHouse — real-time aggregation.** One table `(timestamp, product_id, variant_id, complaint_category, source_url, raw_excerpt)`; one query bucketing complaint volume by week × category to power the live chart, recomputed each time new reviews stream in.
*Why not Postgres:* the pitch is fast repeated OLAP aggregation over live-growing data, recomputed mid-demo — ClickHouse's exact positioning.

**cited.md — publish the action.** On inflection detection, emit a sourced markdown/JSON report; each complaint claim links to the originating review URL. Returns a public permanent URL = the demo payoff. *(Confirm exact API with a sponsor at the event.)*

---

## 5. Scope — build slices (ruthless)

**MUST (the demo lives or dies here)**
1. Tavily search + fetch for ONE chosen product, 1–2 sources. Clean text out.
2. Prometheux: lean rule set (5–8 rules across taste/texture/packaging/price + the date-relative rule) + variant entity resolution. Returns structured classification **with rule-hit trace per review**.
3. ClickHouse: table + the week×category aggregation query.
4. Chart with reformulation date marked + visible inflection.
5. cited.md publish step → public URL with cited claims.

**SHOULD (if time)**
6. Agent finds the reformulation date autonomously via Tavily (vs. a constant). *High autonomy points — worth prioritizing once MUST is green.*

**WON'T (resist the temptation)**
- Multi-product coverage · live monetization/x402 build · ontology authoring UI · auth/multi-tenant · broad source coverage.

---

## 6. Pre-build decision: pick the demo product

Need ONE real product with (a) a documented reformulation/recipe/packaging change on a known date and (b) enough public review chatter that a spike actually exists. Pick something with a vocal fanbase (food/drink reformulations and "they changed the recipe" backlashes are ideal). **Verify the spike is real before the demo — don't cherry-pick live.**

> Ask Claude to surface 2–3 candidate products with documented reformulation dates + chatter.

---

## 7. 3-minute demo script

| Time | Beat |
|---|---|
| 0:00–0:15 | **Problem.** "Brands learn a reformulation backfired in the quarterly review. The complaints were public day one. We catch it in week 2." |
| 0:15–1:30 | **Live autonomous run.** Type *one product name*. Agent searches live, finds the reformulation date itself, fetches reviews, classifies. Narrate the autonomy: "zero hand-curation." |
| 1:30–2:00 | **Hero moment — Prometheux trace.** Click a review: "Here's *why* it was counted as a reformulation complaint — rule X, this lexical marker, dated after the recipe change." Then the chart: inflection lands on the reformulation date. |
| 2:00–2:30 | **The action.** "It doesn't just watch — it publishes." Show the live **cited.md** URL, each claim linked to its source review. |
| 2:30–3:00 | **Tool callouts + close.** Tavily (live retrieval) · Prometheux (explainable classification) · ClickHouse (real-time aggregation) · cited.md (published, sourced action). "Brands subscribe per product; alerts billed via x402." |

---

## 8. Submission checklist (Devpost)

- [ ] 3-minute demo **video**
- [ ] Public **GitHub** repo (built during the event)
- [ ] Devpost project details complete
- [ ] cited.md public URL linked in the writeup (proof of "real action")
- [ ] README names the 3 sponsor tools + what each did

---

## 9. Risk register

| Risk | Mitigation |
|---|---|
| Live Tavily run returns junk / no spike | Pre-validate the product offline; keep a cached fallback run but *present live first*. |
| cited.md API unknown | Confirm with sponsor in first 30 min; if blocked, publish to a simple public page and still call it the "action" layer. |
| Prometheux rules brittle | Keep the rule set small (5–8) and the demo product on-distribution. |
| Out of time | MUST slices only; #6 autonomy is the first thing to cut. |
| "It only observes" critique | The cited.md publish step is the answer — make it explicit in the pitch. |
