"""Reddit mention counts via OAuth-backed search, paginated and time-bucketed.

Requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET (free Reddit "script" app).
Skips gracefully when credentials are absent.
"""
import os
import time
from datetime import datetime, timezone

from common import get_json

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
SEARCH_URL = "https://oauth.reddit.com/search.json"
MAX_RESULTS = 1000
MAX_PAGES = 11


class _RedditToken:
    token = None
    expires = 0


def _get_token(session):
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    if _RedditToken.token and time.time() < _RedditToken.expires - 60:
        return _RedditToken.token
    resp = session.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=30,
        headers={"User-Agent": os.environ.get("USER_AGENT", "bigrank/0.1")},
    )
    resp.raise_for_status()
    body = resp.json()
    _RedditToken.token = body["access_token"]
    _RedditToken.expires = time.time() + body.get("expires_in", 3600)
    return _RedditToken.token


def collect(session, tool):
    query = tool.get("reddit_query")
    if not query:
        return None
    token = _get_token(session)
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    cut7 = now_ts - 7 * 86400
    cut30 = now_ts - 30 * 86400

    counts = {"7d": 0, "30d": 0}
    after = None
    fetched = 0
    for _ in range(MAX_PAGES):
        params = {"q": query, "sort": "new", "limit": 100, "raw_json": 1}
        if after:
            params["after"] = after
        res = get_json(session, SEARCH_URL, headers=headers, params=params)
        children = (res.get("data") or {}).get("children") or []
        if not children:
            break
        fetched += len(children)
        for c in children:
            ts = (c.get("data") or {}).get("created_utc", 0)
            if ts >= cut7:
                counts["7d"] += 1
            if ts >= cut30:
                counts["30d"] += 1
        after = (res.get("data") or {}).get("after")
        if not after or fetched >= MAX_RESULTS:
            break

    return {
        "mentions_7d": counts["7d"],
        "mentions_30d": counts["30d"],
        "capped": fetched >= MAX_RESULTS,
    }
