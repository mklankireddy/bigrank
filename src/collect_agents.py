"""Orchestrate agent collectors into a single daily snapshot.

Usage:
    python src/collect_agents.py                 # collect for today, write snapshot
    python src/collect_agents.py --dry-run       # collect, print summary, do not write
    python src/collect_agents.py --date 2026-08-07
"""
import argparse
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import agent_snapshot_path, consolidate_agents, http_session, load_agent_config  # noqa: E402

from sources import github_agent, hn, reddit  # noqa: E402

COLLECTORS = {
    "github": github_agent.collect,
    "hn": hn.collect,
    "reddit": reddit.collect,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="collect but do not write files")
    ap.add_argument("--date", default=date.today().isoformat(), help="snapshot date (YYYY-MM-DD)")
    args = ap.parse_args()

    cfg = load_agent_config()
    agents = cfg["agents"]
    session = http_session()

    rows = []
    for agent in agents:
        sources_data = {}
        for name, fn in COLLECTORS.items():
            try:
                val = fn(session, agent)
                if val is not None:
                    sources_data[name] = val
            except Exception as e:  # noqa: BLE001 - one bad source must not kill the run
                print(f"  ! {agent['id']}/{name}: {e}", file=sys.stderr)
        rows.append({"date": args.date, "agent": agent["id"], "sources": sources_data})

    if not args.dry_run:
        path = agent_snapshot_path(args.date)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        existing = {}
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        existing[rec["agent"]] = rec
        for rec in rows:
            existing[rec["agent"]] = rec
        with open(path, "w") as f:
            for rec in existing.values():
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"wrote {len(existing)} agent records -> {path}")
        moved, kept = consolidate_agents()
        print(f"retention: moved {moved} day(s) to archive, kept {kept} daily file(s)")
    else:
        print("dry run - nothing written")

    print(f"\nsnapshot for {args.date}: {len(rows)} agents")
    for rec in rows:
        s = rec["sources"]
        parts = []
        if "github" in s:
            g = s["github"]
            parts.append(f"stars={g.get('stars')} commits30d={g.get('commits_30d')}")
            parts.append(f"issues={g.get('issues_opened_30d')}/{g.get('issues_closed_30d')}")
            if g.get("archived"):
                parts.append("ARCHIVED")
        if "hn" in s:
            parts.append(f"hn30d={s['hn'].get('mentions_30d')}")
        if "reddit" in s:
            parts.append(f"rd30d={s['reddit'].get('mentions_30d')}")
        print(f"  {rec['agent']:<22} " + " | ".join(parts))


if __name__ == "__main__":
    main()
