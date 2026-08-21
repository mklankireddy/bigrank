"""Orchestrate local-llm daily snapshots (config audit trail, no network).

Local LLM specs and benchmarks are hand-maintained in config/local-llm.json.
The daily run records one empty-sources record per model so the repo keeps an
auditable day-by-day trail of which models were tracked; the static values are
injected from config at build time (see build_local_llm.py).

Usage:
    python src/collect_local_llm.py                 # collect for today, write snapshot
    python src/collect_local_llm.py --dry-run       # print summary, do not write
    python src/collect_local_llm.py --date 2026-08-20
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import consolidate_llms, load_llm_config, llm_snapshot_path  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print summary but do not write files")
    ap.add_argument("--date", default=date.today().isoformat(), help="snapshot date (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg = load_llm_config()
    models = cfg["models"]

    rows = [{"date": args.date, "model": m["id"], "sources": {}} for m in models]

    if not args.dry_run:
        path = llm_snapshot_path(args.date)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        existing[rec["model"]] = rec
        for rec in rows:
            existing[rec["model"]] = rec
        with open(path, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"wrote {len(existing)} model records -> {path}")
        moved, kept = consolidate_llms()
        print(f"retention: moved {moved} day(s) to archive, kept {kept} daily file(s)")
    else:
        print("dry run - nothing written")

    print(f"\nsnapshot for {args.date}: {len(rows)} models")
    for m in models:
        b = m.get("benchmarks", {})
        print(
            f"  {m['id']:<34} params={m.get('parameters'):<5} "
            f"mmlu={b.get('mmlu')} humaneval={b.get('humaneval')} "
            f"ctx={m.get('context_length')} ram>={m.get('min_ram_gb')}GB "
            f"vram>={m.get('min_vram_gb')}GB"
        )


if __name__ == "__main__":
    main()
