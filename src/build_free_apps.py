"""Render site/ai/apps/free/data.js + index.html from free-app snapshots + config.

The hand-maintained factors (free_tier, ease_of_access, usefulness) are read
from config/free_apps.json and injected into scoring here — they are not part of
the daily snapshot, since they change only when a maintainer edits the config.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    ROOT,
    SITE_DIR,
    VERSION,
    goatcounter_snippet,
    load_free_apps_config,
    load_free_app_snapshots,
    short_commit,
)
from nav import render_nav  # noqa: E402
from score import (  # noqa: E402
    FREE_DELTA_METRICS,
    FREE_METRICS,
    build_series,
    composite,
    coverage,
    raw_and_scores,
)

TEMPLATE = os.path.join(ROOT, "src", "templates", "free_apps.html")
PAGE_DIR = os.path.join(SITE_DIR, "ai", "apps", "free")
PAGE_PATH = "ai/apps/free/index.html"

SERIES_KEYS = ["value", "momentum", "free_tier", "hn_30d"]
EXTRA_METRICS = ["free_tier", "hn_30d"]


def main():
    cfg = load_free_apps_config()
    snaps = load_free_app_snapshots()
    dates = sorted(snaps)
    if not dates:
        print("no free-app snapshots yet; nothing to build")
        return

    latest = dates[-1]
    pivot = dates[max(0, len(dates) - 30)]
    app_ids = [a["id"] for a in cfg["apps"]]

    manual = {
        a["id"]: {
            "free_tier": a.get("manual", {}).get("free_tier"),
            "ease_of_access": a.get("manual", {}).get("ease_of_access"),
            "usefulness": a.get("manual", {}).get("usefulness"),
        }
        for a in cfg["apps"]
    }

    raw, scores = raw_and_scores(
        snaps, cfg, latest, pivot, FREE_METRICS, FREE_DELTA_METRICS, "apps", manual
    )
    cv = composite(scores, cfg["meta"]["weights_value"], app_ids)
    cm = composite(scores, cfg["meta"]["weights_momentum"], app_ids)
    cov_v = coverage(scores, cfg["meta"]["weights_value"], app_ids)
    cov_m = coverage(scores, cfg["meta"]["weights_momentum"], app_ids)
    series = build_series(
        snaps, cfg, FREE_METRICS, FREE_DELTA_METRICS,
        item_key="apps", w_install_key="weights_value",
        w_momentum_key="weights_momentum", series_keys=SERIES_KEYS,
        extra_metrics=EXTRA_METRICS, manual_scores=manual,
    )

    apps_data = []
    for a in cfg["apps"]:
        aid = a["id"]
        apps_data.append({
            "id": aid,
            "name": a["name"],
            "vendor": a.get("vendor"),
            "category": a.get("category"),
            "pricing": a.get("pricing"),
            "homepage": a.get("homepage"),
            "manual": a.get("manual") or {},
            "values": raw[aid],
            "scores": {m: scores[m].get(aid) for m in scores},
            "composite": {"value": cv[aid], "momentum": cm[aid]},
            "coverage": {"value": cov_v[aid], "momentum": cov_m[aid]},
            "series": {k: series[aid][k] for k in SERIES_KEYS},
        })

    data = {
        "meta": {
            "updated": latest,
            "start": dates[0],
            "days": len(dates),
            "repo": os.environ.get("GITHUB_REPOSITORY") or cfg["meta"].get("repo", ""),
            "version": VERSION,
            "build_commit": short_commit(),
            "weights_value": cfg["meta"]["weights_value"],
            "weights_momentum": cfg["meta"]["weights_momentum"],
        },
        "apps": apps_data,
        "dates": dates,
    }

    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(os.path.join(PAGE_DIR, "data.js"), "w") as f:
        f.write("window.FREE_APPS_DATA = " + json.dumps(data) + ";\n")
    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav("free-apps", PAGE_PATH))
    html = html.replace("{{GOATCOUNTER}}", goatcounter_snippet())
    with open(os.path.join(PAGE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built free-apps page for {latest} ({len(dates)} days, {len(apps_data)} apps)")


if __name__ == "__main__":
    main()
