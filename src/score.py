"""Scoring: min-max normalization + weighted composites + time series."""

METRICS = {
    "stars": ("github", "stars"),
    "forks": ("github", "forks"),
    "commits_30d": ("github", "commits_30d"),
    "commit_mentions": ("github", "commit_mentions"),
    "hn_7d": ("hn", "mentions_7d"),
    "hn_30d": ("hn", "mentions_30d"),
    "reddit_7d": ("reddit", "mentions_7d"),
    "reddit_30d": ("reddit", "mentions_30d"),
    "vscode_installs": ("vscode", "installs"),
    "vscode_downloads": ("vscode", "downloads"),
    "vscode_trending_weekly": ("vscode", "trending_weekly"),
    "openvsx_downloads": ("openvsx", "downloads"),
    "jetbrains_downloads": ("jetbrains", "downloads"),
}

DELTA_METRICS = {
    "stars_delta_30d": ("github", "stars"),
    "vscode_installs_delta_30d": ("vscode", "installs"),
}

RUNNER_METRICS = {
    "stars": ("github", "stars"),
    "forks": ("github", "forks"),
    "commits_30d": ("github", "commits_30d"),
    "hn_7d": ("hn", "mentions_7d"),
    "hn_30d": ("hn", "mentions_30d"),
    "reddit_7d": ("reddit", "mentions_7d"),
    "reddit_30d": ("reddit", "mentions_30d"),
    "docker_pulls": ("docker", "pulls"),
    "pypi_downloads": ("pypi", "last_month"),
    "npm_downloads": ("npm", "downloads"),
}

RUNNER_DELTA_METRICS = {
    "stars_delta_30d": ("github", "stars"),
    "docker_pulls_delta_30d": ("docker", "pulls"),
    "pypi_downloads_delta_30d": ("pypi", "last_month"),
    "npm_downloads_delta_30d": ("npm", "downloads"),
}

# Free AI apps: mostly closed products, so automated signals (HN/Reddit/GitHub)
# are blended with hand-maintained factors (free_tier, ease_of_access, usefulness)
# that the build script injects from config/free_apps.json. The latter are always
# present, so they never trigger the coverage penalty.
FREE_METRICS = {
    "stars": ("github", "stars"),
    "hn_7d": ("hn", "mentions_7d"),
    "hn_30d": ("hn", "mentions_30d"),
    "reddit_7d": ("reddit", "mentions_7d"),
    "reddit_30d": ("reddit", "mentions_30d"),
    "free_tier": ("manual", "free_tier"),
    "ease_of_access": ("manual", "ease_of_access"),
    "usefulness": ("manual", "usefulness"),
}

FREE_DELTA_METRICS = {
    "stars_delta_30d": ("github", "stars"),
}


def get_metric(rec, src, key):
    return ((rec or {}).get("sources") or {}).get(src, {}).get(key)


def normalize(values):
    """Min-max normalize a {tool_id: value|None} dict to 0..100 (None stays None)."""
    present = [v for v in values.values() if isinstance(v, (int, float))]
    out = {}
    if not present:
        return {k: None for k in values}
    mn, mx = min(present), max(present)
    for k, v in values.items():
        if not isinstance(v, (int, float)):
            out[k] = None
        elif mx == mn:
            out[k] = 100.0
        else:
            out[k] = round((v - mn) / (mx - mn) * 100, 1)
    return out


def composite(scores, weights, tool_ids):
    """Weighted average of normalized metric scores.

    Missing sources count as 0 (denominator is the FULL weight sum), so a tool
    with data from few sources is capped by the weight those sources carry.
    """
    total = sum(weights.values()) or 1.0
    out = {}
    for tid in tool_ids:
        num = 0.0
        for metric, w in weights.items():
            sc = scores.get(metric, {}).get(tid)
            if sc is not None:
                num += sc * w
        out[tid] = round(num / total, 1)
    return out


def coverage(scores, weights, tool_ids):
    """Fraction of the view's total weight that a tool actually has data for (0-100)."""
    total = sum(weights.values()) or 1.0
    out = {}
    for tid in tool_ids:
        have = sum(
            w for m, w in weights.items() if scores.get(m, {}).get(tid) is not None
        )
        out[tid] = round(have / total * 100, 1)
    return out


def raw_and_scores(snapshots, cfg, latest_date, pivot_date, metrics=METRICS,
                   delta_metrics=DELTA_METRICS, item_key="tools",
                   manual_scores=None):
    """Return (raw, scores) for every metric across tools/runners.

    raw:    {item_id: {metric: value}}
    scores: {metric: {item_id: 0..100}}

    ``manual_scores`` (optional) maps item_id -> {metric: value} for metrics that
    live in config rather than snapshots (e.g. hand-maintained free-app factors).
    They are merged into ``raw`` so they normalize exactly like automated metrics.
    """
    items = cfg[item_key]
    raw = {t["id"]: {} for t in items}
    latest = snapshots[latest_date]
    pivot = snapshots.get(pivot_date, latest)

    for t in items:
        tid = t["id"]
        rec = latest.get(tid, {})
        for metric, (src, key) in metrics.items():
            raw[tid][metric] = get_metric(rec, src, key)
        rec_p = pivot.get(tid, {})
        for metric, (src, key) in delta_metrics.items():
            a = get_metric(rec, src, key)
            b = get_metric(rec_p, src, key)
            raw[tid][metric] = a - b if (a is not None and b is not None) else None

    if manual_scores:
        for tid, vals in manual_scores.items():
            if tid in raw:
                for metric, v in vals.items():
                    if metric in metrics:
                        raw[tid][metric] = v

    all_metrics = set(metrics) | set(delta_metrics)
    scores = {m: normalize({tid: raw[tid][m] for tid in raw}) for m in all_metrics}
    return raw, scores


def build_series(snapshots, cfg, metrics=METRICS, delta_metrics=DELTA_METRICS,
                 item_key="tools", w_install_key="weights_install",
                 w_momentum_key="weights_momentum", series_keys=None,
                 extra_metrics=None, manual_scores=None):
    """Per-item time series of composites + key raw metrics, keyed by date."""
    dates = sorted(snapshots)
    item_ids = [t["id"] for t in cfg[item_key]]
    w_install = cfg["meta"][w_install_key]
    w_momentum = cfg["meta"][w_momentum_key]
    if series_keys is None:
        series_keys = ["install", "momentum", "stars", "hn_30d", "vscode_installs"]
    if extra_metrics is None:
        extra_metrics = ["stars", "hn_30d", "vscode_installs"]
    composite_key = series_keys[0]  # e.g. "install" (tools/runners) or "value" (free apps)
    momentum_key = series_keys[1]

    series = {
        tid: {"dates": dates, **{k: [] for k in series_keys}}
        for tid in item_ids
    }

    for i, d in enumerate(dates):
        pivot = dates[max(0, i - 29)]
        view = {d: snapshots[d], pivot: snapshots[pivot]}
        raw, scores = raw_and_scores(view, cfg, d, pivot, metrics, delta_metrics, item_key, manual_scores)
        ci = composite(scores, w_install, item_ids)
        cm = composite(scores, w_momentum, item_ids)
        for tid in item_ids:
            series[tid][composite_key].append(ci[tid])
            series[tid][momentum_key].append(cm[tid])
            for m in extra_metrics:
                series[tid][m].append(raw[tid][m])

    return series
