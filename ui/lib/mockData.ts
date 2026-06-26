import { RunResult } from "./types";

// Seeded from the REAL validated Tavily run (scripts/validate.py).
// Swap this for Teammate B's live /run when the orchestrator lands.
export const mockRun: RunResult = {
  product: "Reese's Peanut Butter Cups",
  reformulation_date: "2026-02-17",
  inflection: {
    inflection_week: "2026-03-30",
    reformulation_date: "2026-02-17",
    severity: 0.86,
  },
  cited_url: "https://cited.md/r/reformulation-sentinel-reeses-2026", // placeholder until B confirms API
  buckets: [
    { week: "2026-01-26", complaint_category: "taste", count: 1 },
    { week: "2026-02-09", complaint_category: "taste", count: 3 },
    { week: "2026-02-16", complaint_category: "taste", count: 5 },
    { week: "2026-02-16", complaint_category: "texture", count: 2 },
    { week: "2026-02-23", complaint_category: "taste", count: 4 },
    { week: "2026-03-02", complaint_category: "taste", count: 4 },
    { week: "2026-03-02", complaint_category: "texture", count: 1 },
    { week: "2026-03-23", complaint_category: "taste", count: 6 },
    { week: "2026-03-30", complaint_category: "taste", count: 9 },
    { week: "2026-03-30", complaint_category: "texture", count: 3 },
    { week: "2026-04-06", complaint_category: "taste", count: 5 },
    { week: "2026-05-18", complaint_category: "taste", count: 1 },
  ],
  reviews: [
    {
      url: "https://www.goodmorningamerica.com/food/story/reeses-inventors-grandson-accuses-hershey-changing-candy-recipe-130404900",
      variant_id: "reeses-pbc-standard",
      complaint_category: "taste",
      published_date: "2026-02-17",
      rule_trace: [
        "R3 recipe-change-marker: text matches /chang(e|ed) .* recipe/",
        "R7 date-relative: published 2026-02-17 ≥ supersede-date 2026-02-17",
        "→ classified PostReformulationTasteComplaint",
      ],
      raw_excerpt:
        "The grandson of H.B. Reese accuses Hershey of changing the candy recipe for some select items.",
    },
    {
      url: "https://www.bonappetit.com/story/reeses-recipe-change",
      variant_id: "reeses-pbc-standard",
      complaint_category: "taste",
      published_date: "2026-02-19",
      rule_trace: [
        "R1 taste-change-marker: text matches /tasted? different|changed its recipe/",
        "R7 date-relative: published ≥ supersede-date",
        "→ classified PostReformulationTasteComplaint",
      ],
      raw_excerpt:
        "Reese's Has Definitely Changed Its Recipe, Right? You've probably noticed a change.",
    },
    {
      url: "https://www.popsci.com/science/why-candy-tastes-different-now",
      variant_id: "reeses-pbc-standard",
      complaint_category: "texture",
      published_date: "2026-03-30",
      rule_trace: [
        "R2 texture-marker: text matches /waxy|compound coating|not real chocolate/",
        "R7 date-relative: published ≥ supersede-date",
        "→ classified PostReformulationTextureComplaint",
      ],
      raw_excerpt:
        "Why candy tastes different now — Hershey switched some products to cheaper compound coating.",
    },
    {
      url: "https://www.cbsnews.com/news/hershey-keeping-classic-recipe-reeses-criticism",
      variant_id: "reeses-pbc-standard",
      complaint_category: "taste",
      published_date: "2026-04-01",
      rule_trace: [
        "R5 resolution-marker: text matches /shift back|classic recipe|reverse/",
        "→ classified ReformulationReversal (company reaction)",
      ],
      raw_excerpt:
        "Hershey says it will shift back to classic Reese's recipe after backlash.",
    },
  ],
};
