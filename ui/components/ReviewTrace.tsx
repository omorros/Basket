"use client";

import { ArrowUpRight } from "lucide-react";
import { ClassifiedReview } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const VARIANT: Record<string, any> = {
  taste: "taste", texture: "texture", packaging: "packaging", price: "price", none: "default",
};

function prettyDate(d: string | null) {
  if (!d) return "";
  const [y, m, day] = d.split("-");
  const months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[parseInt(m, 10)]} ${parseInt(day, 10)}, ${y}`;
}

export default function ReviewTrace({
  reviews, selected, onSelect,
}: {
  reviews: ClassifiedReview[];
  selected: number;
  onSelect: (i: number) => void;
}) {
  const r = reviews[selected];

  return (
    <div className="grid gap-8 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
      {/* evidence list */}
      <div>
        <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Evidence
        </p>
        <div className="space-y-1.5">
          {reviews.map((rv, i) => (
            <button
              key={rv.url}
              onClick={() => onSelect(i)}
              className={cn(
                "w-full rounded-xl border px-4 py-3 text-left transition-colors",
                i === selected ? "border-foreground/15 bg-muted" : "border-transparent hover:bg-muted/60"
              )}
            >
              <div className="mb-1.5 flex items-center gap-2">
                <Badge variant={VARIANT[rv.complaint_category]} className="capitalize">
                  {rv.complaint_category}
                </Badge>
                <span className="tnum text-xs text-muted-foreground">{prettyDate(rv.published_date)}</span>
              </div>
              <p className="line-clamp-2 text-sm leading-snug text-foreground/80">
                {rv.raw_excerpt}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* the reasoning */}
      <div>
        <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Why it was counted
        </p>
        <div className="rounded-2xl border bg-muted/40 p-5">
          <p className="mb-4 text-sm leading-relaxed text-foreground">
            &ldquo;{r.raw_excerpt}&rdquo;
          </p>
          <ol className="space-y-2.5">
            {r.rule_trace.map((t, i) => {
              const verdict = t.startsWith("→");
              return (
                <li key={i} className="flex gap-3 text-[13px] leading-relaxed">
                  <span className="tnum select-none pt-0.5 text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className={cn("font-mono", verdict ? "font-medium text-critical" : "text-foreground/70")}>
                    {t.replace(/^→\s*/, "")}
                  </span>
                </li>
              );
            })}
          </ol>
          <a
            href={r.url} target="_blank" rel="noreferrer"
            className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            View source <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
