"""JetBrains Marketplace plugin download counts (official plugin IDs only)."""
from common import get_json

API = "https://plugins.jetbrains.com/api"


def collect(session, tool):
    spec = tool.get("jetbrains")
    if not spec:
        return None
    res = get_json(session, f"{API}/plugins/{spec['plugin_id']}")
    return {
        "downloads": res.get("downloads"),
        "rating": res.get("rating"),
        "updated": res.get("cdate"),
    }
