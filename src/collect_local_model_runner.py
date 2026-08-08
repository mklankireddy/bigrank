"""Orchestrate local-model-runner collectors into a single daily snapshot.

Usage:
    python src/collect_local_model_runner.py                 # collect for today, write snapshot
    python src/collect_local_model_runner.py --dry-run       # collect, print summary, do not write
    python src/collect_local_model_runner.py --date 2026-08-07
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import consolidate_runners, http_session, load_runner_config, runner_snapshot_path  # noqa: E402

from sources import docker, github_runner, hn, npm, pypi, reddit  # noqa: E402

COLLECTORS = {
    "github": github_runner.collect,
    "hn": hn.collect,
    "reddit": reddit.collect,
    "docker": docker.collect,
    "pypi": pypi.collect,
    "npm": npm.collect,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="collect but do not write files")
    ap.add_argument("--date", default=date.today().isoformat(), help="snapshot date (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg = load_runner_config()
    runners = cfg["runners"]
    session = http_session()

    rows = []
    for runner in runners:
        sources_data = {}
        for name, fn in COLLECTORS.items():
            try:
                val = fn(session, runner)
                if val is not None:
                    sources_data[name] = val
            except Exception as e:  # noqa: BLE001 - one bad source must not kill the run
                print(f"  ! {runner['id']}/{name}: {e}", file=sys.stderr)
        rows.append({"date": args.date, "runner": runner["id"], "sources": sources_data})

    if not args.dry_run:
        path = runner_snapshot_path(args.date)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        existing[rec["runner"]] = rec
        for rec in rows:
            existing[rec["runner"]] = rec
        with open(path, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"wrote {len(existing)} runner records -> {path}")
        moved, kept = consolidate_runners()
        print(f"retention: moved {moved} day(s) to archive, kept {kept} daily file(s)")
    else:
        print("dry run - nothing written")

    print(f"\nsnapshot for {args.date}: {len(rows)} runners")
    for rec in rows:
        s = rec["sources"]
        parts = []
        if "github" in s:
            parts.append(f"stars={s['github'].get('stars')} commits30d={s['github'].get('commits_30d')}")
        if "hn" in s:
            parts.append(f"hn30d={s['hn'].get('mentions_30d')}")
        if "reddit" in s:
            parts.append(f"rd30d={s['reddit'].get('mentions_30d')}")
        if "docker" in s:
            parts.append(f"docker_pulls={s['docker'].get('pulls')}")
        if "pypi" in s:
            parts.append(f"pypi_m={s['pypi'].get('last_month')}")
        if "npm" in s:
            parts.append(f"npm_m={s['npm'].get('downloads')}")
        print(f"  {rec['runner']:<22} " + " | ".join(parts))


if __name__ == "__main__":
    main()
