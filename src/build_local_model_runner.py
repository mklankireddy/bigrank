"""Render site/ai/model/local-model-runner/data.js + index.html from runner snapshots."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT, SITE_DIR, VERSION, load_runner_config, load_runner_snapshots, short_commit  # noqa: E402
from nav import render_nav  # noqa: E402
from score import RUNNER_DELTA_METRICS, RUNNER_METRICS, build_series, composite, coverage, raw_and_scores  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "templates", "local_model_runner.html")
PAGE_DIR = os.path.join(SITE_DIR, "ai", "model", "local-model-runner")
PAGE_PATH = "ai/model/local-model-runner/index.html"

SERIES_KEYS = ["install", "momentum", "stars", "docker_pulls", "pypi_downloads", "hn_30d"]
EXTRA_METRICS = ["stars", "docker_pulls", "pypi_downloads", "hn_30d"]


def main():
    cfg = load_runner_config()
    snaps = load_runner_snapshots()
    dates = sorted(snaps)
    if not dates:
        print("no runner snapshots yet; nothing to build")
        return

    latest = dates[-1]
    pivot = dates[max(0, len(dates) - 30)]
    runner_ids = [r["id"] for r in cfg["runners"]]

    raw, scores = raw_and_scores(snaps, cfg, latest, pivot, RUNNER_METRICS, RUNNER_DELTA_METRICS, "runners")
    ci = composite(scores, cfg["meta"]["weights_install"], runner_ids)
    cm = composite(scores, cfg["meta"]["weights_momentum"], runner_ids)
    cov_i = coverage(scores, cfg["meta"]["weights_install"], runner_ids)
    cov_m = coverage(scores, cfg["meta"]["weights_momentum"], runner_ids)
    series = build_series(
        snaps, cfg, RUNNER_METRICS, RUNNER_DELTA_METRICS,
        item_key="runners", series_keys=SERIES_KEYS, extra_metrics=EXTRA_METRICS,
    )

    runners_data = []
    for r in cfg["runners"]:
        rid = r["id"]
        runners_data.append({
            "id": rid,
            "name": r["name"],
            "vendor": r.get("vendor"),
            "category": r.get("category"),
            "pricing": r.get("pricing"),
            "homepage": r.get("homepage"),
            "tags": r.get("tags"),
            "values": raw[rid],
            "scores": {m: scores[m].get(rid) for m in scores},
            "composite": {"install": ci[rid], "momentum": cm[rid]},
            "coverage": {"install": cov_i[rid], "momentum": cov_m[rid]},
            "series": {k: series[rid][k] for k in SERIES_KEYS},
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
        "runners": runners_data,
        "dates": dates,
    }

    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(os.path.join(PAGE_DIR, "data.js"), "w") as f:
        f.write("window.LOCAL_MODEL_RUNNER_DATA = " + json.dumps(data) + ";\n")
    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav("local-model-runner", PAGE_PATH))
    with open(os.path.join(PAGE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built local-model-runner page for {latest} ({len(dates)} days, {len(runners_data)} runners)")


if __name__ == "__main__":
    main()
