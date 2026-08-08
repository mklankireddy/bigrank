"""Docker Hub pull/star counts via the public Hub v2 API (no auth required)."""
from common import get_json

API = "https://hub.docker.com/v2/repositories"


def collect(session, runner):
    spec = runner.get("docker")
    if not spec:
        return None
    res = get_json(session, f"{API}/{spec['namespace']}/{spec['name']}")
    return {
        "pulls": res.get("pull_count"),
        "stars": res.get("star_count"),
        "updated": res.get("last_updated"),
    }
