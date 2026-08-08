"""PyPI download counts via PyPI Stats (free, no auth, ~60s cache)."""
from common import get_json_fast

API = "https://pypistats.org/api/packages"


def collect(session, runner):
    spec = runner.get("pypi")
    if not spec:
        return None
    res = get_json_fast(session, f"{API}/{spec['package']}/recent")
    data = res.get("data") or {}
    return {
        "last_day": data.get("last_day"),
        "last_week": data.get("last_week"),
        "last_month": data.get("last_month"),
    }
