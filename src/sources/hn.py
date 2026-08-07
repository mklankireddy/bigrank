"""Hacker News mention counts via the Algolia API (free, no auth)."""
from datetime import datetime, timedelta, timezone

from common import get_json

API = "https://hn.algolia.com/api/v1/search"


def collect(session, tool):
    query = tool.get("hn_query")
    if not query:
        return None

    now = int(datetime.now(timezone.utc).timestamp())
    data = {}
    for label, days in (("7", 7), ("30", 30)):
        cutoff = now - days * 86400
        res = get_json(
            session,
            API,
            params={
                "query": query,
                "tags": "comment",
                "numericFilters": f"created_at_i>{cutoff}",
                "advancedSyntax": "true",
            },
        )
        data[f"mentions_{label}d"] = res.get("nbHits")
    return data
