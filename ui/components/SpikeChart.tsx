"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, CartesianGrid,
} from "recharts";
import { WeeklyBucket, Inflection } from "@/lib/types";

// Monochrome blue family keeps the chart quiet; red is reserved for the peak.
const CATS: { key: string; label: string; fill: string }[] = [
  { key: "taste", label: "Taste", fill: "hsl(211 100% 45%)" },
  { key: "texture", label: "Texture", fill: "hsl(205 90% 73%)" },
  { key: "packaging", label: "Packaging", fill: "hsl(150 45% 55%)" },
  { key: "price", label: "Price", fill: "hsl(40 90% 60%)" },
];

function fmt(week: string) {
  const [, m, d] = week.split("-");
  const months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[parseInt(m, 10)]} ${parseInt(d, 10)}`;
}

function pivot(buckets: WeeklyBucket[]) {
  const present = new Set<string>();
  const byWeek: Record<string, any> = {};
  for (const b of buckets) {
    present.add(b.complaint_category);
    byWeek[b.week] ??= { week: b.week };
    byWeek[b.week][b.complaint_category] =
      (byWeek[b.week][b.complaint_category] ?? 0) + b.count;
  }
  const rows = Object.values(byWeek).sort((a: any, z: any) => (a.week < z.week ? -1 : 1));
  return { rows, cats: CATS.filter((c) => present.has(c.key)) };
}

function nearestWeek(rows: any[], date: string) {
  let best = rows[0]?.week;
  for (const r of rows) if (r.week <= date) best = r.week;
  return best;
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border bg-card px-3 py-2 text-xs shadow-sm">
      <div className="mb-1 font-medium">Week of {fmt(label)}</div>
      {payload.map((p: any) => (
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
  const { rows, cats } = pivot(buckets);
  const reformWeek = nearestWeek(rows, inflection.reformulation_date);

  return (
    <div className="h-[320px] w-full">
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ top: 28, right: 12, left: -16, bottom: 4 }} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke="hsl(240 11% 91%)" />
          <XAxis
            dataKey="week" tickFormatter={fmt} tickLine={false} axisLine={false}
            tick={{ fontSize: 11, fill: "hsl(240 2% 44%)" }} dy={6}
          />
          <YAxis
            tickLine={false} axisLine={false} width={36} allowDecimals={false}
            tick={{ fontSize: 11, fill: "hsl(240 2% 44%)" }}
          />
          <Tooltip cursor={{ fill: "hsl(240 6% 96%)" }} content={<CustomTooltip />} />
          {cats.map((c, i) => (
            <Bar
              key={c.key} dataKey={c.key} stackId="a" fill={c.fill}
              radius={i === cats.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
              isAnimationActive animationDuration={750} animationEasing="ease-out"
            />
          ))}
          <ReferenceLine
            x={reformWeek} stroke="hsl(240 6% 11%)" strokeDasharray="3 3"
            label={{ value: "Reformulation", fontSize: 11, fill: "hsl(240 6% 11%)", position: "top" }}
          />
          <ReferenceLine
            x={inflection.inflection_week} stroke="hsl(4 78% 52%)" strokeWidth={1.5}
            label={{ value: "Peak", fontSize: 11, fill: "hsl(4 78% 52%)", position: "top" }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
