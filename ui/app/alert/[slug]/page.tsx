import Link from "next/link";
import { RunResult } from "@/lib/types";
import { mockRun } from "@/lib/mockData";

export const dynamic = "force-dynamic";

const ORCHESTRATOR = process.env.ORCHESTRATOR_URL ?? "http://localhost:8000";
const MONTHS = ["", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

function prettyDate(iso?: string | null) {
  if (!iso) return "unknown";
  const [y, m, d] = iso.split("-");
  return `${MONTHS[parseInt(m, 10)]?.slice(0, 3)} ${parseInt(d, 10)}, ${y}`;
}

const CAT: Record<string, string> = {
  taste: "bg-primary/10 text-primary",
  texture: "bg-sky-100 text-sky-700",
  packaging: "bg-emerald-50 text-emerald-700",
  price: "bg-amber-50 text-amber-700",
};

async function getData(product: string): Promise<RunResult> {
  try {
    const r = await fetch(`${ORCHESTRATOR}/run?product=${encodeURIComponent(product)}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    if (!r.ok) throw new Error(`orchestrator ${r.status}`);
    return await r.json();
  } catch {
    return { ...mockRun, product };
  }
}

export default async function AlertPage({
  params, searchParams,
}: {
  params: { slug: string };
  searchParams: { p?: string };
}) {
  const product = searchParams.p
    ? decodeURIComponent(searchParams.p)
    : params.slug.replace(/-/g, " ");
  const data = await getData(product);
  const complaints = data.reviews.filter((r) => r.complaint_category !== "none");
  const sev = data.inflection ? Math.round(data.inflection.severity) : 0;

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
        ← Reformulation Sentinel
      </Link>

      <article className="mt-8">
        <p className="text-xs font-medium uppercase tracking-wide text-critical">
          Reformulation alert
        </p>
        <h1 className="mt-2 text-3xl font-semibold leading-tight tracking-tightest">
          {data.product}
        </h1>
        <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
          Complaint volume rose{" "}
          <span className="font-semibold text-critical">{sev}×</span> above baseline after the{" "}
          {MONTHS[parseInt((data.reformulation_date || "0-0").split("-")[1], 10)]}{" "}
          reformulation, peaking the week of{" "}
          <span className="font-medium text-foreground">
            {prettyDate(data.inflection?.inflection_week)}
          </span>
          . This report is generated from live public sources; every claim links to its origin.
        </p>

        <dl className="mt-6 grid grid-cols-2 gap-4 rounded-2xl border bg-card p-5 sm:grid-cols-4">
          {[
            ["Reformulation", prettyDate(data.reformulation_date)],
            ["Peak week", prettyDate(data.inflection?.inflection_week)],
            ["Severity", `${sev}× baseline`],
            ["Cited sources", `${complaints.length}`],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">{k}</dt>
              <dd className="tnum mt-1 text-[15px] font-medium">{v}</dd>
            </div>
          ))}
        </dl>

        <h2 className="mt-10 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Cited complaints
        </h2>
        <ul className="mt-4 space-y-5">
          {complaints.map((r) => (
            <li key={r.url} className="border-l-2 border-border pl-4">
              <div className="mb-1 flex items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${CAT[r.complaint_category] ?? "bg-muted text-muted-foreground"}`}>
                  {r.complaint_category}
                </span>
                <span className="tnum text-xs text-muted-foreground">{prettyDate(r.published_date)}</span>
              </div>
              <p className="text-[15px] leading-snug text-foreground/90">&ldquo;{r.raw_excerpt}&rdquo;</p>
              {r.rule_trace?.length > 0 && (
                <p className="mt-1.5 font-mono text-xs text-muted-foreground">
                  {r.rule_trace[r.rule_trace.length - 1].replace(/^→\s*/, "")}
                </p>
              )}
              <a href={r.url} target="_blank" rel="noreferrer"
                 className="mt-1 inline-block text-xs font-medium text-primary hover:underline">
                Source ↗
              </a>
            </li>
          ))}
        </ul>

        <div className="mt-10">
          <a
            href={`/alert/${params.slug}/raw?p=${encodeURIComponent(product)}`}
            target="_blank" rel="noreferrer"
            className="text-sm font-medium text-primary hover:underline"
          >
            Download as Markdown ↓
          </a>
        </div>

        <footer className="mt-8 border-t pt-6 text-xs leading-relaxed text-muted-foreground">
          Generated by Reformulation Sentinel. Mentions retrieved via Tavily live web search,
          classified by Prometheux declarative rules (each complaint linked to the rule that
          fired), aggregated and spike-detected in ClickHouse.
        </footer>
      </article>
    </main>
  );
}
