import { NextResponse } from "next/server";
import { mockRun } from "@/lib/mockData";

export const dynamic = "force-dynamic";

// The FastAPI orchestrator (Agent 0). Override with ORCHESTRATOR_URL in prod.
const ORCHESTRATOR = process.env.ORCHESTRATOR_URL ?? "http://localhost:8000";

export async function GET(req: Request) {
  const product =
    new URL(req.url).searchParams.get("product") ?? mockRun.product;
  try {
    const res = await fetch(
      `${ORCHESTRATOR}/run?product=${encodeURIComponent(product)}`,
      { signal: AbortSignal.timeout(90_000), cache: "no-store" }
    );
    if (!res.ok) throw new Error(`orchestrator ${res.status}`);
    const data = await res.json();
    return NextResponse.json({ ...data, _source: "live" });
  } catch (e: any) {
    // Demo safety net: never blank the screen if the orchestrator is down.
    console.error("[run] orchestrator unreachable, using mock:", e?.message);
    return NextResponse.json({ ...mockRun, product, _source: "mock-fallback" });
  }
}
