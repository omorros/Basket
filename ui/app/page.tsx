"use client";

import { useRef, useState } from "react";
import { Search, X } from "lucide-react";
import SpikeChart from "@/components/SpikeChart";
import ReviewTrace from "@/components/ReviewTrace";
import PipelineStatus from "@/components/PipelineStatus";
import { RunResult } from "@/lib/types";
import { useCountUp } from "@/lib/useCountUp";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const MONTHS = ["", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

function monthName(iso: string) {
  return MONTHS[parseInt(iso.split("-")[1], 10)] ?? "";
}
function prettyDate(iso: string) {
  const [y, m, d] = iso.split("-");
  return `${MONTHS[parseInt(m, 10)].slice(0, 3)} ${parseInt(d, 10)}, ${y}`;
}

function Reveal({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <div
      className="animate-in fade-in slide-in-from-bottom-4 fill-mode-both"
      style={{ animationDuration: "600ms", animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="tnum mt-1 text-[15px] font-medium text-foreground">{value}</p>
    </div>
  );
}

export default function Home() {
  const [product, setProduct] = useState("Reese's Peanut Butter Cups");
  const [data, setData] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const sev = data ? Math.round(data.inflection.severity) : 0;
  const count = Math.round(useCountUp(sev, 1100));

  async function run() {
    if (!product.trim() || loading) return;
    setLoading(true);
    setData(null);
    try {
      const res = await fetch(`/api/run?product=${encodeURIComponent(product)}`);
      setData(await res.json());
      setSelected(0);
    } finally {
      setLoading(false);
    }
  }

  function newSearch() {
    setData(null);
    setProduct("");
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <header className="mb-12 animate-in fade-in slide-in-from-bottom-3 fill-mode-both duration-700">
        <p className="mb-4 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Reformulation Sentinel
        </p>
        <h1 className="max-w-xl text-3xl font-semibold leading-tight tracking-tightest text-foreground sm:text-[2.6rem]">
          Catch a reformulation backlash in week two, not the quarterly review.
        </h1>
        <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-muted-foreground">
          Enter a product. The agent finds when its recipe changed, reads what people
          are saying across the web, and flags the moment sentiment turns.
        </p>
      </header>

      <div className="flex gap-2.5 animate-in fade-in fill-mode-both duration-700 delay-150">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
            placeholder="Product name"
            className="pl-11 pr-10"
          />
          {product && (
            <button
              onClick={newSearch}
              aria-label="Clear"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button onClick={run} disabled={loading || !product.trim()} className="transition-transform active:scale-95">
          {loading ? "Analyzing" : data ? "Search again" : "Analyze"}
        </Button>
      </div>

      {data && !loading && (
        <button
          onClick={newSearch}
          className="mt-3 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          Start a new search
        </button>
      )}

      {loading && (
        <Card className="mt-10 animate-in fade-in zoom-in-95 fill-mode-both duration-500">
          <CardHeader>
            <CardTitle>Running the agent</CardTitle>
            <CardDescription>Acting on live data, no hand-curation.</CardDescription>
          </CardHeader>
          <CardContent>
            <PipelineStatus />
          </CardContent>
        </Card>
      )}

      {data && !loading && (
        <div className="mt-12 space-y-6">
          <Reveal delay={0}>
            <Card className="overflow-hidden">
              <CardContent className="pt-6">
                <p className="text-xl font-medium leading-snug tracking-tight text-foreground sm:text-2xl">
                  Complaints about {data.product} rose{" "}
                  <span className="tnum text-critical">{count}&times;</span> after the{" "}
                  {monthName(data.reformulation_date)} reformulation, peaking the week of{" "}
                  {prettyDate(data.inflection.inflection_week)}.
                </p>
                <Separator className="my-5" />
                <div className="grid grid-cols-2 gap-y-5 sm:grid-cols-4">
                  <Stat label="Reformulation" value={prettyDate(data.reformulation_date)} />
                  <Stat label="Peak week" value={prettyDate(data.inflection.inflection_week)} />
                  <Stat label="Severity" value={`${sev}× baseline`} />
                  <Stat label="Sources" value={`${data.reviews.length} cited`} />
                </div>
              </CardContent>
            </Card>
          </Reveal>

          <Reveal delay={90}>
            <Card>
              <CardHeader>
                <CardTitle>Complaint volume by week</CardTitle>
                <CardDescription>
                  Grouped by complaint type. The dashed line marks the reformulation.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SpikeChart buckets={data.buckets} inflection={data.inflection} />
              </CardContent>
            </Card>
          </Reveal>

          <Reveal delay={180}>
            <Card>
              <CardContent className="pt-6">
                <ReviewTrace reviews={data.reviews} selected={selected} onSelect={setSelected} />
              </CardContent>
            </Card>
          </Reveal>

          <Reveal delay={270}>
            <Card>
              <CardHeader>
                <CardTitle>Published alert</CardTitle>
                <CardDescription>
                  On detecting the inflection, the agent published a sourced report. Each claim
                  links to its originating mention.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <a
                  href={data.cited_url} target="_blank" rel="noreferrer"
                  className="text-sm font-medium text-primary hover:underline"
                >
                  {data.cited_url}
                </a>
              </CardContent>
            </Card>
          </Reveal>
        </div>
      )}
    </main>
  );
}
