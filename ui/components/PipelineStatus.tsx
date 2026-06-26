"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { label: "Finding the reformulation date", tool: "Tavily" },
  { label: "Retrieving mentions across the web", tool: "Tavily" },
  { label: "Classifying complaints by rule", tool: "Prometheux" },
  { label: "Aggregating volume by week", tool: "ClickHouse" },
  { label: "Publishing the sourced alert", tool: "cited.md" },
];

// Visual progress for the multi-agent run. Advances on a timer so the demo
// reads as a live pipeline; the final step holds until real data lands.
export default function PipelineStatus() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(
      () => setActive((a) => Math.min(a + 1, STEPS.length - 1)),
      2200
    );
    return () => clearInterval(id);
  }, []);

  return (
    <ol className="space-y-1">
      {STEPS.map((s, i) => {
        const done = i < active;
        const current = i === active;
        return (
          <li
            key={s.label}
            className={cn(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors duration-500",
              current && "bg-muted"
            )}
          >
            <span
              className={cn(
                "flex h-5 w-5 items-center justify-center rounded-full transition-colors",
                done && "bg-primary text-primary-foreground",
                current && "text-primary",
                !done && !current && "text-muted-foreground"
              )}
            >
              {done ? (
                <Check className="h-3 w-3" />
              ) : current ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-current opacity-40" />
              )}
            </span>
            <span
              className={cn(
                "text-sm transition-colors",
                done || current ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {s.label}
            </span>
            <span className="ml-auto text-xs text-muted-foreground">{s.tool}</span>
          </li>
        );
      })}
    </ol>
  );
}
