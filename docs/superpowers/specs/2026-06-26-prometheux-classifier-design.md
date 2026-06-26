# Prometheux Classifier — Design Spec

**Date:** 2026-06-26 · **Owner:** Nicole · **Branch:** `prometheux-classifier`
**Project:** Reformulation Sentinel (LDN Hack). This is Agent 3, the demo's hero component
(see `PRD (1).md` §4, §7 and `TEAM.md`).

## Purpose

Turn raw product reviews into classified, *traceable* rows using a Prometheux/Vadalog
knowledge graph. Success = for the chosen demo product, every review gets a complaint
category and a human-readable rule-trace explaining why, and the output validates against
the frozen data contract so Agent 4 ingests it without changes.

Two jobs:
1. **Entity resolution** — collapse variant aliases ("Reese's" / "Reese's Peanut Butter Cups"
   / "Reeses") into one variant node; know which variant *supersedes* which (the edge carries
   the reformulation date).
2. **Rule classification + trace** — assign each review a complaint category via declarative
   rules, and emit the rule-trace (the hero moment).

## Scope

**In scope:** the classifier module only — ontology, Vadalog rules, the Python adapter, seed
tables for ONE demo product, mock fixtures, tests.

**Out of scope (mock against the contract):** web retrieval (Agent 2 / Tavily), aggregation
and inflection detection (Agent 4 / ClickHouse), publishing (Agent 5 / cited.md).

## Frozen data contract (do not change)

```python
# IN  (Agent 2 -> us)
Review = {url, source, text, published_date, product_query}   # published_date ISO 8601

# OUT (us -> Agent 4)
ClassifiedReview = {
  url, variant_id,
  complaint_category,     # "taste"|"texture"|"packaging"|"price"|"none"
  published_date,
  rule_trace: list[str],  # which rules fired + why  <-- HERO MOMENT
  raw_excerpt,            # snippet that triggered the rule
}
```

## The knowledge graph (ontology)

Nodes: **Product**, **Variant** (aliases resolve here), **Review**, **ComplaintType**
(taste|texture|packaging|price|none), **Marker** (a lexical trigger phrase, typed by the
ComplaintType it signals).

Edges:
- `Variant --instanceOf--> Product`
- `Variant --supersedes--> Variant`  (attribute: `reformulation_date`)
- `Review --aboutVariant--> Variant`  (output of entity resolution)
- `Review --mentions--> ComplaintType` (output of marker matching)

Why this beats an LLM classifier (the pitch): entity resolution is a graph join, not fuzzy
string-matching; every classification is explainable as a literal rule-trace back to source
text + date, not "the model said so."

Locked demo target (TEAM.md): Reese's Peanut Butter Cups (Hershey), a live 2026
reformulation (milk chocolate to cheaper compound coating). Reform date 2026-02-17.

## The Vadalog rules (5-8, kept lean per PRD risk register)

Facts loaded by the adapter:
```
review(Url, Source, Text, Date, Query).
alias(AliasString, VariantId).
supersedes(NewVariant, OldVariant, ReformDate).
marker(Phrase, Category).
```

Rules (sketch — exact built-ins confirmed at sponsor booth):
- **A. Entity resolution:** `about(Url,V) <- review(Url,_,_,_,Q), alias(A,V), contains(Q,A).`
- **B. Marker hit:** `hit(Url,Cat,P) <- review(Url,_,T,_,_), marker(P,Cat), contains(T,P).`
- **C. Date-relative (differentiator):**
  `post_reform(Url,Cat) <- about(Url,V), hit(Url,Cat,_), supersedes(V,_,RD), review(Url,_,_,D,_), D >= RD.`
- **D. Classification head:** assemble `classified(Url,V,Cat,Date,Excerpt)`; `@output("classified")`.

## Trace strategy (hero moment) — built-in, not hand-rolled

Prometheux provides provenance via `@explain` (per-fact derivation chain) and `@model`
(turns a predicate into a readable sentence). So `rule_trace[]` is populated from the engine,
not written by hand. Target trace:
```
1. "Reese's Peanut Butter Cups" in the query resolves to variant reeses-compound-2026 (rule A).
2. reeses-compound-2026 supersedes reeses-classic, reformulated 2026-02-17 (supersedes edge).
3. Review text contains "changed the recipe" -> taste marker (rule B).
4. Review dated 2026-03-01 >= 2026-02-17 -> post-reformulation taste complaint (rule C).
```

## Architecture (de-risked for the hackathon)

A thin Python adapter over the engine, with the engine hidden behind a 4-method interface
(`save / run / fetch / explain`). A `MockPxClient` mirrors the interface and simulates the
Vadalog semantics in plain Python, so the whole module is buildable and testable *today*,
before the token or teammates are ready. Swapping to the real `prometheux_chain` SDK touches
one file (`px_client.py`). No other file changes on swap.

```
classifier/
  contract.py    # TypedDicts + a validate() for the frozen contract
  px_client.py   # PxClient protocol; MockPxClient (now) + RealPxClient (token swap)
  seeds.py       # alias / supersedes / marker tables for the demo product
  rules.vada     # the Vadalog program (rules A-D + @explain/@model)
  adapter.py     # classify(reviews) -> ClassifiedReview[]
  fixtures/reviews.json
  tests/
```

## Open dependencies / risks

- **Sponsor booth (first 30 min):** confirm SDK auth + exact built-ins (string-contains,
  date-compare, negation for "none"). Top dependency.
- **Provenance JSON shape:** map real `@explain` output (Fact / JsonExplanation /
  TextualExplanation) into `rule_trace[]`; `@model` sentences are the easy path. Verify on a
  real run before relying on it for the demo.
- **Demo product pick:** drives the seed tables and whether a real spike exists. Validate the
  spike offline first (PRD §6, owned by Nicole as Agent 2).
- **Brittleness:** keep to 5-8 rules; keep the demo product on-distribution (PRD risk).
