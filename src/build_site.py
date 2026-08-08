"""Render site/ai/agents/coding/data.js + site/ai/agents/coding/index.html from the snapshot history."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT, SITE_DIR, VERSION, goatcounter_snippet, load_config, load_snapshots, short_commit  # noqa: E402
from nav import render_nav  # noqa: E402
import score  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "templates", "index.html")
PAGE_DIR = os.path.join(SITE_DIR, "ai", "agents", "coding")
PAGE_PATH = "ai/agents/coding/index.html"


def main():
    cfg = load_config()
    snaps = load_snapshots()
    dates = sorted(snaps)
    if not dates:
        print("no snapshots yet; nothing to build")
        return

    latest = dates[-1]
    pivot = dates[max(0, len(dates) - 30)]
    tool_ids = [t["id"] for t in cfg["tools"]]

    raw, scores = score.raw_and_scores(snaps, cfg, latest, pivot)
    ci = score.composite(scores, cfg["meta"]["weights_install"], tool_ids)
    cm = score.composite(scores, cfg["meta"]["weights_momentum"], tool_ids)
    cov_i = score.coverage(scores, cfg["meta"]["weights_install"], tool_ids)
    cov_m = score.coverage(scores, cfg["meta"]["weights_momentum"], tool_ids)
    series = score.build_series(snaps, cfg)

    tools_data = []
    for t in cfg["tools"]:
        tid = t["id"]
        tools_data.append({
            "id": tid,
            "name": t["name"],
            "vendor": t.get("vendor"),
            "category": t.get("category"),
            "pricing": t.get("pricing"),
            "homepage": t.get("homepage"),
            "values": raw[tid],
            "scores": {m: scores[m].get(tid) for m in scores},
            "composite": {"install": ci[tid], "momentum": cm[tid]},
            "coverage": {"install": cov_i[tid], "momentum": cov_m[tid]},
            "series": {k: series[tid][k] for k in ("install", "momentum", "stars", "hn_30d", "vscode_installs")},
        })

    data = {
        "meta": {
            "updated": latest,
            "start": dates[0],
            "days": len(dates),
            "repo": os.environ.get("GITHUB_REPOSITORY") or cfg["meta"].get("repo", ""),
            "version": VERSION,
            "build_commit": short_commit(),
            "weights_install": cfg["meta"]["weights_install"],
            "weights_momentum": cfg["meta"]["weights_momentum"],
        },
        "tools": tools_data,
        "dates": dates,
    }

    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(os.path.join(PAGE_DIR, "data.js"), "w") as f:
        f.write("window.RANKING_DATA = " + json.dumps(data) + ";\n")
    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav("coding", PAGE_PATH))
    html = html.replace("{{GOATCOUNTER}}", goatcounter_snippet())
    with open(os.path.join(PAGE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built site for {latest} ({len(dates)} days, {len(tools_data)} tools)")


if __name__ == "__main__":
    main()
