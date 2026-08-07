"""Orchestrate all collectors into a single daily snapshot.

Usage:
    python src/collect.py                 # collect for today, write snapshot
    python src/collect.py --dry-run       # collect, print summary, do not write
    python src/collect.py --date 2026-08-07
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import consolidate_snapshots, http_session, load_config, snapshot_path  # noqa: E402

from sources import github, hn, jetbrains, openvsx, reddit, vscode  # noqa: E402

COLLECTORS = {
    "github": github.collect,
    "hn": hn.collect,
    "reddit": reddit.collect,
    "vscode": vscode.collect,
    "openvsx": openvsx.collect,
    "jetbrains": jetbrains.collect,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="collect but do not write files")
    ap.add_argument("--date", default=date.today().isoformat(), help="snapshot date (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg = load_config()
    tools = cfg["tools"]
    session = http_session()

    rows = []
    for tool in tools:
        sources_data = {}
        for name, fn in COLLECTORS.items():
            try:
                val = fn(session, tool)
                if val is not None:
                    sources_data[name] = val
            except Exception as e:  # noqa: BLE001 - one bad source must not kill the run
                print(f"  ! {tool['id']}/{name}: {e}", file=sys.stderr)
        rows.append({"date": args.date, "tool": tool["id"], "sources": sources_data})

    if not args.dry_run:
        path = snapshot_path(args.date)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        existing[rec["tool"]] = rec
        for rec in rows:
            existing[rec["tool"]] = rec
        with open(path, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"wrote {len(existing)} tool records -> {path}")
        moved, kept = consolidate_snapshots()
        print(f"retention: moved {moved} day(s) to archive, kept {kept} daily file(s)")
    else:
        print("dry run - nothing written")

    print(f"\nsnapshot for {args.date}: {len(rows)} tools")
    for rec in rows:
        s = rec["sources"]
        parts = []
        if "github" in s:
            parts.append(f"stars={s['github'].get('stars')}")
        if "hn" in s:
            parts.append(f"hn7d={s['hn'].get('mentions_7d')}")
        if "reddit" in s:
            parts.append(f"rd7d={s['reddit'].get('mentions_7d')}")
        if "vscode" in s:
            parts.append(f"vscode_install={s['vscode'].get('installs')}")
        if "openvsx" in s:
            parts.append(f"ovsx_dl={s['openvsx'].get('downloads')}")
        if "jetbrains" in s:
            parts.append(f"jb_dl={s['jetbrains'].get('downloads')}")
        print(f"  {rec['tool']:<16} " + " | ".join(parts))


if __name__ == "__main__":
    main()
