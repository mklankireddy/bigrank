"""GitHub signals for local model runners: stars, forks, own-repo commit velocity."""
from datetime import datetime, timedelta, timezone

from common import get_json

from sources.github import _commit_count_search, _headers, _pace

API = "https://api.github.com"


def collect(session, runner):
    repo = (runner.get("github") or {}).get("repo")
    if not repo:
        return None

    info = get_json(session, f"{API}/repos/{repo}", headers=_headers())
    data = {
        "stars": info.get("stargazers_count"),
        "forks": info.get("forks_count"),
        "open_issues": info.get("open_issues_count"),
        "archived": bool(info.get("archived")),
        "pushed_at": info.get("pushed_at"),
    }

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    _pace()
    try:
        data["commits_30d"] = _commit_count_search(session, repo, since)
    except Exception:
        data["commits_30d"] = None

    return data
