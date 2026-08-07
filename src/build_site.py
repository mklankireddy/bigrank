"""Render site/index.html + site/data.js from the snapshot history."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT, SITE_DIR, load_config, load_snapshots  # noqa: E402
import score  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "templates", "index.html")


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
            "weights_install": cfg["meta"]["weights_install"],
            "weights_momentum": cfg["meta"]["weights_momentum"],
        },
        "tools": tools_data,
        "dates": dates,
    }

    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, "data.js"), "w") as f:
        f.write("window.RANKING_DATA = " + json.dumps(data) + ";\n")
    with open(TEMPLATE) as f:
        html = f.read()
    with open(os.path.join(SITE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built site for {latest} ({len(dates)} days, {len(tools_data)} tools)")


if __name__ == "__main__":
    main()
