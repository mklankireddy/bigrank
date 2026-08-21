"""Render site/ai/model/local-llm/data.js + index.html for the Local LLM ranking.

All scored values (mmlu, humaneval, context_length) are hand-maintained in
config/local-llm.json and injected into scoring here via manual_scores — they
are not part of the daily snapshot, since they change only when a maintainer
edits the config.
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
    load_llm_config,
    load_llm_snapshots,
    short_commit,
)
from nav import render_nav  # noqa: E402
from score import LLM_METRICS, build_series, composite, coverage, raw_and_scores  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "templates", "local_llm.html")
PAGE_DIR = os.path.join(SITE_DIR, "ai", "model", "local-llm")
PAGE_PATH = "ai/model/local-llm/"

# build_series requires both composite keys and every extra metric to be
# listed here; capability appears twice because there is no second view.
SERIES_KEYS = ["capability", "capability", "mmlu", "humaneval"]
EXTRA_METRICS = ["mmlu", "humaneval"]


def main():
    cfg = load_llm_config()
    snaps = load_llm_snapshots()
    dates = sorted(snaps)
    if not dates:
        print("no local-llm snapshots yet; nothing to build")
        return

    latest = dates[-1]
    pivot = dates[max(0, len(dates) - 30)]
    model_ids = [m["id"] for m in cfg["models"]]

    manual = {
        m["id"]: {
            "mmlu": m.get("benchmarks", {}).get("mmlu"),
            "humaneval": m.get("benchmarks", {}).get("humaneval"),
            "context_length": m.get("context_length"),
        }
        for m in cfg["models"]
    }

    raw, scores = raw_and_scores(
        snaps, cfg, latest, pivot, LLM_METRICS, {}, "models", manual
    )
    cc = composite(scores, cfg["meta"]["weights_capability"], model_ids)
    cov_c = coverage(scores, cfg["meta"]["weights_capability"], model_ids)
    series = build_series(
        snaps, cfg, LLM_METRICS, {},
        item_key="models",
        w_install_key="weights_capability", w_momentum_key="weights_capability",
        series_keys=SERIES_KEYS, extra_metrics=EXTRA_METRICS, manual_scores=manual,
    )

    models_data = []
    for m in cfg["models"]:
        mid = m["id"]
        models_data.append({
            "id": mid,
            "name": m["name"],
            "vendor": m.get("vendor"),
            "parameters": m.get("parameters"),
            "parameters_b": m.get("parameters_b"),
            "license": m.get("license"),
            "quant_formats": m.get("quant_formats") or [],
            "min_ram_gb": m.get("min_ram_gb"),
            "min_vram_gb": m.get("min_vram_gb"),
            "context_length": m.get("context_length"),
            "best_use_case": m.get("best_use_case"),
            "last_benchmark_update": m.get("last_benchmark_update"),
            "benchmarks_note": m.get("benchmarks_note"),
            "homepage": m.get("homepage"),
            "pricing": m.get("pricing"),
            "values": raw[mid],
            "scores": {k: scores[k].get(mid) for k in scores},
            "composite": {"capability": cc[mid]},
            "coverage": {"capability": cov_c[mid]},
            "series": {"capability": series[mid]["capability"]},
        })

    data = {
        "meta": {
            "updated": latest,
            "start": dates[0],
            "days": len(dates),
            "repo": os.environ.get("GITHUB_REPOSITORY") or cfg["meta"].get("repo", ""),
            "version": VERSION,
            "build_commit": short_commit(),
            "weights_capability": cfg["meta"]["weights_capability"],
        },
        "models": models_data,
        "dates": dates,
    }

    os.makedirs(PAGE_DIR, exist_ok=True)
    with open(os.path.join(PAGE_DIR, "data.js"), "w") as f:
        f.write("window.LOCAL_LLM_DATA = " + json.dumps(data) + ";\n")
    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav("local-llm", PAGE_PATH))
    html = html.replace("{{GOATCOUNTER}}", goatcounter_snippet())
    with open(os.path.join(PAGE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"built local-llm page for {latest} ({len(dates)} days, {len(models_data)} models)")


if __name__ == "__main__":
    main()
