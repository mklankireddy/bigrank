"""GitHub signals: stars/forks, own-repo commit velocity, commit-message mentions."""
import os
import time
from datetime import datetime, timedelta, timezone

from common import get_json

API = "https://api.github.com"
PREVIEW = "application/vnd.github.cloak-preview+json"


def _headers():
    h = {
        "Accept": f"{PREVIEW}, application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _pace():
    """Search API: 10 req/min unauthenticated, 30/min with token."""
    if not os.environ.get("GITHUB_TOKEN"):
        time.sleep(6.5)


def _commit_count_search(session, repo, since):
    res = get_json(
        session,
        f"{API}/search/commits",
        headers=_headers(),
        params={"q": f"repo:{repo} committer-date:>{since}", "per_page": 1},
    )
    return res.get("total_count")


def _commit_count_fallback(session, repo, since):
    """Count commits via the commits list endpoint (Link header last-page trick)."""
    resp = session.get(
        f"{API}/repos/{repo}/commits",
        headers=_headers(),
        params={"since": since + "T00:00:00Z", "per_page": 1},
        timeout=30,
    )
    resp.raise_for_status()
    link = resp.headers.get("Link", "")
    for part in link.split(","):
        if 'rel="last"' in part:
            url = part[part.index("<") + 1:part.index(">")]
            last = url.split("page=")[-1].split("&")[0]
            return int(last) if last.isdigit() else None
    return None


def collect(session, tool):
    repo = (tool.get("github") or {}).get("repo")
    if not repo:
        return None

    data = {}
    info = get_json(session, f"{API}/repos/{repo}", headers=_headers())
    data["stars"] = info.get("stargazers_count")
    data["forks"] = info.get("forks_count")
    data["pushed_at"] = info.get("pushed_at")

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    _pace()
    try:
        data["commits_30d"] = _commit_count_search(session, repo, since)
    except Exception:
        _pace()
        data["commits_30d"] = _commit_count_fallback(session, repo, since)

    try:
        _pace()
        term = '"' + " ".join(tool["name"].lower().split()) + '"'
        mentions = get_json(
            session,
            f"{API}/search/commits",
            headers=_headers(),
            params={"q": term, "per_page": 1},
        )
        data["commit_mentions"] = mentions.get("total_count")
    except Exception:
        data["commit_mentions"] = None

    return data
