// TS mirror of agent/schemas.py — keep in sync with the team contract.

export type ClassifiedReview = {
  url: string;
  variant_id: string;
  complaint_category: "taste" | "texture" | "packaging" | "price" | "none";
  published_date: string | null;
  rule_trace: string[];
  raw_excerpt: string;
};

export type WeeklyBucket = {
  week: string; // ISO week start, e.g. "2026-02-16"
  complaint_category: string;
  count: number;
};

export type Inflection = {
  inflection_week: string;
  reformulation_date: string;
  severity: number;
};

// Shape returned by GET /run?product=
export type RunResult = {
  product: string;
  reformulation_date: string;
  reviews: ClassifiedReview[];
  buckets: WeeklyBucket[];
  inflection: Inflection;
  cited_url: string;
};
