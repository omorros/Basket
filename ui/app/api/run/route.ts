import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";
import { mockRun } from "@/lib/mockData";

export const dynamic = "force-dynamic";

const REPO_ROOT = path.resolve(process.cwd(), "..");
const PYTHON = process.env.PYTHON_BIN ?? "python";

// Run the live Python pipeline (real Tavily) and return its JSON.
// When Teammate B's HTTP orchestrator is up, swap this for a fetch to it.
function runPipeline(product: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON, ["-m", "agent.pipeline", product], {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let out = "";
    let err = "";
    proc.stdout.on("data", (d) => (out += d));
    proc.stderr.on("data", (d) => (err += d));
    const timer = setTimeout(() => proc.kill(), 45000);
    proc.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) return reject(new Error(err || `exit ${code}`));
      try {
        resolve(JSON.parse(out.trim().split("\n").pop() as string));
      } catch (e) {
        reject(new Error(`bad JSON: ${out.slice(0, 200)}`));
      }
    });
    proc.on("error", reject);
  });
}

export async function GET(req: Request) {
  const product =
    new URL(req.url).searchParams.get("product") ?? mockRun.product;
  try {
    const data = await runPipeline(product);
    return NextResponse.json({ ...data, _source: "live" });
  } catch (e: any) {
    // Demo safety net: never blank the screen on a live API hiccup.
    console.error("[pipeline] falling back to mock:", e?.message);
    return NextResponse.json({ ...mockRun, product, _source: "mock-fallback" });
  }
}
