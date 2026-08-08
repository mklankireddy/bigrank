"""Render site/ai/agents/general/data.js + site/ai/agents/general/index.html from agent snapshots."""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT, SITE_DIR, VERSION, goatcounter_snippet, load_agent_config, load_agent_snapshots, short_commit  # noqa: E402
from nav import render_nav  # noqa: E402
from score import composite, normalize  # noqa: E402

AGENTS_TEMPLATE = os.path.join(ROOT, "src", "templates", "agents.html")
AGENTS_DIR = os.path.join(SITE_DIR, "ai", "agents", "general")
AGENTS_PAGE_PATH = "ai/agents/general/index.html"

AGENT_METRICS = {
    "stars": ("github", "stars"),
    "forks_30d": ("github", "forks_30d"),
    "subscribers": ("github", "subscribers"),
    "commits_30d": ("github", "commits_30d"),
    "issues_opened_30d": ("github", "issues_opened_30d"),
    "issues_closed_30d": ("github", "issues_closed_30d"),
    "hn_30d": ("hn", "mentions_30d"),
    "reddit_30d": ("reddit", "mentions_30d"),
}


def _get_metric(rec, src, key):
    return ((rec or {}).get("sources") or {}).get(src, {}).get(key)


def freshness(rec):
    g = (rec.get("sources") or {}).get("github") or {}
    if g.get("archived"):
        return "archived"
    last = g.get("last_commit")
    if not last:
        return "stale"
    try:
        dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - dt).days
    except Exception:
        return "steady"
    if age <= 7:
        return "active"
    if age <= 30:
        return "steady"
    if age <= 60:
        return "slowing"
    return "stale"


def main():
    cfg = load_agent_config()
    snaps = load_agent_snapshots()
    dates = sorted(snaps)
    if not dates:
        print("no agent snapshots yet; nothing to build")
        return

    latest = dates[-1]
    agent_ids = [a["id"] for a in cfg["agents"]]
    wa = cfg["meta"]["weights_activity"]
    wad = cfg["meta"]["weights_adoption"]

    raw = {}
    for a in cfg["agents"]:
        rec = snaps[latest].get(a["id"], {})
        raw[a["id"]] = {m: _get_metric(rec, src, key) for m, (src, key) in AGENT_METRICS.items()}

    scores = {m: normalize({aid: raw[aid][m] for aid in agent_ids}) for m in AGENT_METRICS}
    activity = composite(scores, wa, agent_ids)
    adoption = composite(scores, wad, agent_ids)
    overall = {aid: round(0.5 * activity[aid] + 0.5 * adoption[aid], 1) for aid in agent_ids}

    agents_data = []
    for a in cfg["agents"]:
        aid = a["id"]
        rec = snaps[latest].get(aid, {})
        g = (rec.get("sources") or {}).get("github") or {}
        agents_data.append({
            "id": aid,
            "name": a["name"],
            "vendor": a.get("vendor"),
            "category": a.get("category"),
            "pricing": a.get("pricing"),
            "homepage": a.get("homepage"),
            "setup": a.get("setup"),
            "effort": a.get("effort"),
            "values": raw[aid],
            "scores": {"activity": activity[aid], "adoption": adoption[aid], "overall": overall[aid]},
            "freshness": freshness(rec),
            "open_issues": g.get("open_issues"),
            "latest_release": g.get("latest_release"),
            "last_commit": g.get("last_commit"),
        })

    data = {
        "meta": {
            "updated": latest,
            "start": dates[0],
            "days": len(dates),
            "repo": os.environ.get("GITHUB_REPOSITORY") or cfg["meta"].get("repo", ""),
            "version": VERSION,
            "build_commit": short_commit(),
            "weights_activity": wa,
            "weights_adoption": wad,
        },
        "agents": agents_data,
        "dates": dates,
    }

    os.makedirs(AGENTS_DIR, exist_ok=True)
    with open(os.path.join(AGENTS_DIR, "data.js"), "w") as f:
        f.write("window.AGENTS_DATA = " + json.dumps(data) + ";\n")
    with open(AGENTS_TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav("general", AGENTS_PAGE_PATH))
    html = html.replace("{{GOATCOUNTER}}", goatcounter_snippet())
    with open(os.path.join(AGENTS_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built agents page for {latest} ({len(dates)} days, {len(agents_data)} agents)")


if __name__ == "__main__":
    main()
