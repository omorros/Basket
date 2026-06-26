"""Smoke test: confirm Prometheux auth + a trivial Vadalog run, and ClickHouse connectivity.

Run BEFORE wiring the real classifier, to de-risk credentials and learn the live
response shapes:

    cd ~/Desktop/Basket && ./.venv/bin/python -m scripts.px_smoke

Reads PMTX_TOKEN / JARVISPY_URL / CLICKHOUSE_* from .env. Prints what works and
what does not, with the exact error, so we fix creds before building on them.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_prometheux() -> bool:
    token = os.environ.get("PMTX_TOKEN", "").strip()
    url = os.environ.get("JARVISPY_URL", "").strip()
    if not token or "{org}" in url or not url:
        print("[prometheux] SKIP: set PMTX_TOKEN and a real JARVISPY_URL in .env first")
        return False
    try:
        import prometheux_chain as px
        os.environ["PMTX_TOKEN"] = token
        px.config.set("JARVISPY_URL", url)

        pid = px.save_project(project_name="reformulation_sentinel_smoke")
        definition = (
            'company("Apple", "Cupertino").\n'
            'company("Google", "Mountain View").\n'
            "location(L) :- company(_, L).\n"
            '@output("location").\n'
        )
        px.save_concept(project_id=pid, definition=definition, concept_name="location")
        px.run_concept(project_id=pid, concept_name="location")
        rows = px.fetch_results(project_id=pid, output_predicate="location")
        print(f"[prometheux] OK: auth works, project={pid}")
        print(f"[prometheux] fetch_results type={type(rows).__name__}, value={rows!r}")
        return True
    except Exception as e:
        print(f"[prometheux] FAIL: {type(e).__name__}: {e}")
        return False


def check_clickhouse() -> bool:
    if not (os.environ.get("CLICKHOUSE_HOST") and os.environ.get("CLICKHOUSE_PASSWORD")):
        print("[clickhouse] SKIP: set CLICKHOUSE_HOST and CLICKHOUSE_PASSWORD in .env first")
        return False
    try:
        from agent import clickhouse_store as ch
        client = ch.get_client()
        ver = client.query("SELECT version()").result_rows[0][0]
        print(f"[clickhouse] OK: connected, server version {ver}")
        return True
    except Exception as e:
        print(f"[clickhouse] FAIL: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    ok_px = check_prometheux()
    ok_ch = check_clickhouse()
    print("\nsummary:", "prometheux", "OK" if ok_px else "not-ready", "|",
          "clickhouse", "OK" if ok_ch else "not-ready")
    sys.exit(0 if (ok_px and ok_ch) else 1)
