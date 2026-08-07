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


def raw_and_scores(snapshots, cfg, latest_date, pivot_date):
    """Return (raw, scores) for every metric across tools.

    raw:    {tool_id: {metric: value}}
    scores: {metric: {tool_id: 0..100}}
    """
    tools = cfg["tools"]
    raw = {t["id"]: {} for t in tools}
    latest = snapshots[latest_date]
    pivot = snapshots.get(pivot_date, latest)

    for t in tools:
        tid = t["id"]
        rec = latest.get(tid, {})
        for metric, (src, key) in METRICS.items():
            raw[tid][metric] = get_metric(rec, src, key)
        rec_p = pivot.get(tid, {})
        for metric, (src, key) in DELTA_METRICS.items():
            a = get_metric(rec, src, key)
            b = get_metric(rec_p, src, key)
            raw[tid][metric] = a - b if (a is not None and b is not None) else None

    all_metrics = set(METRICS) | set(DELTA_METRICS)
    scores = {m: normalize({tid: raw[tid][m] for tid in raw}) for m in all_metrics}
    return raw, scores


def build_series(snapshots, cfg):
    """Per-tool time series of composites + key raw metrics, keyed by date."""
    dates = sorted(snapshots)
    tool_ids = [t["id"] for t in cfg["tools"]]
    w_install = cfg["meta"]["weights_install"]
    w_momentum = cfg["meta"]["weights_momentum"]

    series = {
        tid: {"dates": dates, "install": [], "momentum": [], "stars": [], "hn_30d": [], "vscode_installs": []}
        for tid in tool_ids
    }

    for i, d in enumerate(dates):
        pivot = dates[max(0, i - 29)]
        view = {d: snapshots[d], pivot: snapshots[pivot]}
        raw, scores = raw_and_scores(view, cfg, d, pivot)
        ci = composite(scores, w_install, tool_ids)
        cm = composite(scores, w_momentum, tool_ids)
        for tid in tool_ids:
            series[tid]["install"].append(ci[tid])
            series[tid]["momentum"].append(cm[tid])
            series[tid]["stars"].append(raw[tid]["stars"])
            series[tid]["hn_30d"].append(raw[tid]["hn_30d"])
            series[tid]["vscode_installs"].append(raw[tid]["vscode_installs"])

    return series
