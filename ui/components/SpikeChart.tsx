"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, CartesianGrid,
} from "recharts";
import { WeeklyBucket, Inflection } from "@/lib/types";

// Monochrome blue family keeps the chart quiet; the tallest bar is the spike.
const CATS: { key: string; label: string; fill: string }[] = [
  { key: "taste", label: "Taste", fill: "hsl(211 100% 45%)" },
  { key: "texture", label: "Texture", fill: "hsl(205 90% 73%)" },
  { key: "packaging", label: "Packaging", fill: "hsl(150 45% 55%)" },
  { key: "price", label: "Price", fill: "hsl(40 90% 60%)" },
];

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function fmt(week: string) {
  const [, m, d] = week.split("-");
  return `${MON[parseInt(m, 10) - 1]} ${parseInt(d, 10)}`;
}
function addDays(iso: string, n: number) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + n);
  return dt.toISOString().slice(0, 10);
}

// Build a CONTINUOUS weekly series (fill empty weeks with 0) so the timeline
// reads evenly instead of floating bars with gaps.
function buildSeries(buckets: WeeklyBucket[]) {
  const present = new Set<string>();
  const byWeek: Record<string, any> = {};
  for (const b of buckets) {
    present.add(b.complaint_category);
    byWeek[b.week] ??= {};
    byWeek[b.week][b.complaint_category] =
      (byWeek[b.week][b.complaint_category] ?? 0) + b.count;
  }
  const cats = CATS.filter((c) => present.has(c.key));
  const sorted = Object.keys(byWeek).sort();
  if (!sorted.length) return { rows: [], cats };

  const rows: any[] = [];
  let w = sorted[0];
  const last = sorted[sorted.length - 1];
  let guard = 0;
  while (w <= last && guard < 80) {
    const row: any = { week: w };
    for (const c of cats) row[c.key] = byWeek[w]?.[c.key] ?? 0;
    rows.push(row);
    w = addDays(w, 7);
    guard++;
  }
  return { rows, cats };
}

function nearestWeek(rows: any[], date: string) {
  let best = rows[0]?.week;
  for (const r of rows) if (r.week <= date) best = r.week;
  return best;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s: number, p: any) => s + (p.value ?? 0), 0);
  if (!total) return null;
  return (
    <div className="rounded-xl border bg-card px-3 py-2 text-xs shadow-sm">
      <div className="mb-1 font-medium">Week of {fmt(label)}</div>
      {payload.filter((p: any) => p.value > 0).map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ background: p.fill }} />
          <span className="capitalize">{p.dataKey}</span>
          <span className="tnum ml-auto text-foreground">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function SpikeChart({
  buckets, inflection,
}: {
  buckets: WeeklyBucket[];
  inflection: Inflection;
}) {
  const { rows, cats } = buildSeries(buckets);
  const reformWeek = nearestWeek(rows, inflection.reformulation_date);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ top: 24, right: 16, left: -12, bottom: 4 }} barCategoryGap="22%">
          <CartesianGrid vertical={false} stroke="hsl(240 11% 92%)" />
          <XAxis
            dataKey="week" tickFormatter={fmt} tickLine={false} axisLine={false}
            interval="preserveStartEnd" minTickGap={24}
            tick={{ fontSize: 11, fill: "hsl(240 2% 44%)" }} dy={6}
          />
          <YAxis
            tickLine={false} axisLine={false} width={32} allowDecimals={false}
            tick={{ fontSize: 11, fill: "hsl(240 2% 44%)" }}
          />
          <Tooltip cursor={{ fill: "hsl(240 6% 96%)" }} content={<CustomTooltip />} />
          {cats.map((c, i) => (
            <Bar
              key={c.key} dataKey={c.key} stackId="a" fill={c.fill}
              radius={i === cats.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
              isAnimationActive animationDuration={700} animationEasing="ease-out"
            />
          ))}
          <ReferenceLine
            x={reformWeek} stroke="hsl(4 78% 52%)" strokeWidth={1.5} strokeDasharray="4 3"
            label={{ value: "Reformulation", fontSize: 11, fill: "hsl(4 78% 52%)",
                     position: "insideTopRight", offset: 8 }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
