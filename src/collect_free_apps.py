"""Orchestrate free-app collectors into a single daily snapshot.

Most free AI apps are closed products, so the snapshot only carries automated
public signals (GitHub where a repo exists, HN/Reddit mentions). The hand-
maintained factors (free_tier, ease_of_access, usefulness) live in
config/free_apps.json and are merged in at build time — they are not snapshotted.

Usage:
    python src/collect_free_apps.py                 # collect for today, write snapshot
    python src/collect_free_apps.py --dry-run       # collect, print summary, do not write
    python src/collect_free_apps.py --date 2026-08-07
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import consolidate_free_apps, free_app_snapshot_path, http_session, load_free_apps_config  # noqa: E402

from sources import github_runner, hn, reddit  # noqa: E402

COLLECTORS = {
    "github": github_runner.collect,
    "hn": hn.collect,
    "reddit": reddit.collect,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="collect but do not write files")
    ap.add_argument("--date", default=date.today().isoformat(), help="snapshot date (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg = load_free_apps_config()
    apps = cfg["apps"]
    session = http_session()

    rows = []
    for app in apps:
        sources_data = {}
        for name, fn in COLLECTORS.items():
            try:
                val = fn(session, app)
                if val is not None:
                    sources_data[name] = val
            except Exception as e:  # noqa: BLE001 - one bad source must not kill the run
                print(f"  ! {app['id']}/{name}: {e}", file=sys.stderr)
        rows.append({"date": args.date, "app": app["id"], "sources": sources_data})

    if not args.dry_run:
        path = free_app_snapshot_path(args.date)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        existing[rec["app"]] = rec
        for rec in rows:
            existing[rec["app"]] = rec
        with open(path, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"wrote {len(existing)} app records -> {path}")
        moved, kept = consolidate_free_apps()
        print(f"retention: moved {moved} day(s) to archive, kept {kept} daily file(s)")
    else:
        print("dry run - nothing written")

    print(f"\nsnapshot for {args.date}: {len(rows)} apps")
    for rec in rows:
        s = rec["sources"]
        parts = []
        if "github" in s:
            parts.append(f"stars={s['github'].get('stars')} commits30d={s['github'].get('commits_30d')}")
        if "hn" in s:
            parts.append(f"hn30d={s['hn'].get('mentions_30d')}")
        if "reddit" in s:
            parts.append(f"rd30d={s['reddit'].get('mentions_30d')}")
        print(f"  {rec['app']:<16} " + " | ".join(parts))


if __name__ == "__main__":
    main()
