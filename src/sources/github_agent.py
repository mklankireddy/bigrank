"""GitHub signals for open-source agents: repo health, velocity, and adoption."""
from datetime import datetime, timedelta, timezone

from common import get_json

from sources.github import _commit_count_search, _headers, _pace

API = "https://api.github.com"


def _last_commit_date(session, repo):
    resp = session.get(
        f"{API}/repos/{repo}/commits",
        headers=_headers(),
        params={"per_page": 1},
        timeout=30,
    )
    resp.raise_for_status()
    commits = resp.json()
    if not commits:
        return None
    return commits[0]["commit"]["committer"]["date"]


def _issue_search_count(session, repo, query):
    res = get_json(
        session,
        f"{API}/search/issues",
        headers=_headers(),
        params={"q": f"repo:{repo} {query}", "per_page": 1},
    )
    return res.get("total_count")


def _forks_30d(session, repo, since):
    resp = session.get(
        f"{API}/repos/{repo}/forks",
        headers=_headers(),
        params={"sort": "newest", "per_page": 100},
        timeout=30,
    )
    resp.raise_for_status()
    return sum(1 for f in resp.json() if (f.get("created_at") or "")[:10] >= since)


def _latest_release(session, repo):
    try:
        res = get_json(session, f"{API}/repos/{repo}/releases/latest", headers=_headers())
        return res.get("published_at")
    except Exception:
        return None


def collect(session, agent):
    repo = (agent.get("github") or {}).get("repo")
    if not repo:
        return None

    info = get_json(session, f"{API}/repos/{repo}", headers=_headers())
    data = {
        "stars": info.get("stargazers_count"),
        "forks": info.get("forks_count"),
        "subscribers": info.get("subscribers_count"),
        "open_issues": info.get("open_issues_count"),
        "archived": bool(info.get("archived")),
        "pushed_at": info.get("pushed_at"),
    }

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        data["last_commit"] = _last_commit_date(session, repo)
    except Exception:
        data["last_commit"] = None

    _pace()
    try:
        data["commits_30d"] = _commit_count_search(session, repo, since)
    except Exception:
        data["commits_30d"] = None

    _pace()
    try:
        data["issues_opened_30d"] = _issue_search_count(session, repo, f"is:issue created:>{since}")
    except Exception:
        data["issues_opened_30d"] = None

    _pace()
    try:
        data["issues_closed_30d"] = _issue_search_count(session, repo, f"is:issue is:closed closed:>{since}")
    except Exception:
        data["issues_closed_30d"] = None

    try:
        data["forks_30d"] = _forks_30d(session, repo, since)
    except Exception:
        data["forks_30d"] = None

    data["latest_release"] = _latest_release(session, repo)

    return data
