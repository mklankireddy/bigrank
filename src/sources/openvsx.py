"""Open VSX registry download counts (open-source VS Code marketplace)."""
from common import get_json

API = "https://open-vsx.org/api"


def collect(session, tool):
    spec = tool.get("openvsx")
    if not spec:
        return None
    res = get_json(session, f"{API}/{spec['namespace']}/{spec['name']}")
    return {
        "downloads": res.get("downloadCount"),
        "reviews": res.get("reviewCount"),
        "timestamp": res.get("timestamp"),
    }
