"""npm download counts via the public npm downloads API (no auth)."""
from common import get_json

API = "https://api.npmjs.org/downloads/point/last-month"


def collect(session, runner):
    spec = runner.get("npm")
    if not spec:
        return None
    res = get_json(session, f"{API}/{spec['package']}")
    return {
        "downloads": res.get("downloads"),
        "start": res.get("start"),
        "end": res.get("end"),
    }
