import json
import os
import time
from datetime import date

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "tools.json")
DATA_DIR = os.path.join(ROOT, "data", "coding-agents_snapshots")
ARCHIVE_PATH = os.path.join(ROOT, "data", "archives", "coding-agents_archive.jsonl")
SITE_DIR = os.path.join(ROOT, "site")
AGENT_CONFIG_PATH = os.path.join(ROOT, "config", "agents.json")
AGENT_DATA_DIR = os.path.join(ROOT, "data", "general-purpose-agents_snapshots")
AGENT_ARCHIVE_PATH = os.path.join(ROOT, "data", "archives", "general-purpose-agents_archive.jsonl")
RUNNER_CONFIG_PATH = os.path.join(ROOT, "config", "local-model-runner.json")
RUNNER_DATA_DIR = os.path.join(ROOT, "data", "local-model-runner_snapshots")
RUNNER_ARCHIVE_PATH = os.path.join(ROOT, "data", "archives", "local-model-runner_archive.jsonl")
FREE_APPS_CONFIG_PATH = os.path.join(ROOT, "config", "free_apps.json")
FREE_APPS_DATA_DIR = os.path.join(ROOT, "data", "free-apps_snapshots")
FREE_APPS_ARCHIVE_PATH = os.path.join(ROOT, "data", "archives", "free-apps_archive.jsonl")

USER_AGENT = "bigrank/0.1 (+https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "bigrank") + ")"
TIMEOUT = 30

VERSION = "1.7.0"

# GoatCounter analytics (https://www.goatcounter.com). Set to your site code
# (e.g. "bigrank") to enable the tracking snippet on every page; empty = off.
GOATCOUNTER_CODE = os.environ.get("GOATCOUNTER_CODE", "bigmakstech")


def goatcounter_snippet():
    """Return the GoatCounter tracking snippet, or "" when no site code is set."""
    if not GOATCOUNTER_CODE:
        return ""
    return (
        f'<script data-goatcounter="https://{GOATCOUNTER_CODE}.goatcounter.com/count"\n'
        f'        async src="//gc.zgo.at/count.js"></script>\n'
    )


def short_commit():
    sha = os.environ.get("GITHUB_SHA", "")
    if not sha:
        try:
            import subprocess
            sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=ROOT, stderr=subprocess.DEVNULL,
            ).decode().strip()
        except Exception:
            sha = ""
    return sha[:8] or None


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def http_session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def get_json(session, url, **kwargs):
    """GET with retry/backoff for rate limits (429/403), 5xx, and connection errors."""
    kwargs.setdefault("timeout", TIMEOUT)
    last = None
    for attempt in range(4):
        try:
            resp = session.get(url, **kwargs)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (403, 429):
                last = resp
                time.sleep(30 * (attempt + 1))
                continue
            if resp.status_code >= 500:
                last = resp
                time.sleep(10 * (attempt + 1))
                continue
            resp.raise_for_status()
        except requests.RequestException as e:
            last = e
            time.sleep(5 * (attempt + 1))
            continue
    raise RuntimeError(f"failed after retries: {last} {url}")


def get_json_fast(session, url, attempts=2, **kwargs):
    """GET with a short retry schedule; raises after ~5s total.

    For third-party stats APIs (PyPI Stats) that rate-limit aggressively: a
    429 becomes a fast failure, so the caller can record None for the day
    rather than stall the whole daily run on backoff sleeps.
    """
    kwargs.setdefault("timeout", 15)
    last = None
    for attempt in range(attempts):
        try:
            resp = session.get(url, **kwargs)
            if resp.status_code == 200:
                return resp.json()
            last = resp
            if resp.status_code in (403, 429):
                time.sleep(2 * (attempt + 1))
                continue
            if resp.status_code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
        except requests.RequestException as e:
            last = e
            time.sleep(2 * (attempt + 1))
            continue
    raise RuntimeError(f"failed after retries: {last} {url}")


def snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(DATA_DIR, str(d) + ".jsonl")


def _load_archive(archive_path=ARCHIVE_PATH, item_key="tool"):
    """Return {date_str: {item_id: rec}} from a consolidated archive file."""
    out = {}
    if not os.path.exists(archive_path):
        return out
    with open(archive_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out.setdefault(rec["date"], {})[rec[item_key]] = rec
    return out


def _load_daily_files(data_dir, item_key, out):
    """Merge daily snapshot files from `data_dir` into `out` (per-item override)."""
    if not os.path.isdir(data_dir):
        return out
    for fn in sorted(os.listdir(data_dir)):
        if not fn.endswith(".jsonl"):
            continue
        day = fn[:-6]  # strip ".jsonl"
        out.setdefault(day, {})
        with open(os.path.join(data_dir, fn)) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                out[day][rec[item_key]] = rec
    return out


def load_snapshots():
    """Return {date_str: {tool_id: snapshot}}.

    Merges the consolidated archive with the daily snapshot files; daily files
    win on overlap (in practice the windows never overlap).
    """
    return _load_daily_files(DATA_DIR, "tool", _load_archive())


def load_agent_config():
    with open(AGENT_CONFIG_PATH, "r") as f:
        return json.load(f)


def agent_snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(AGENT_DATA_DIR, str(d) + ".jsonl")


def load_agent_snapshots():
    """Return {date_str: {agent_id: rec}} (archive + daily, daily wins)."""
    return _load_daily_files(AGENT_DATA_DIR, "agent", _load_archive(AGENT_ARCHIVE_PATH, "agent"))


def _consolidate(data_dir, archive_path, keep_days, today, item_key):
    """Move daily snapshot files older than the retention window into the archive.

    Daily files are kept for `keep_days` calendar dates (today inclusive); anything
    older is appended to the archive and the daily file is deleted. Dates already
    present in the archive are skipped, so re-runs cannot duplicate rows.
    Returns (moved, kept) counts.
    """
    cutoff = today.toordinal() - (keep_days - 1)
    if not os.path.isdir(data_dir):
        return 0, 0
    archived = _load_archive(archive_path, item_key)
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    moved = kept = 0
    with open(archive_path, "a") as arch:
        for fn in sorted(os.listdir(data_dir)):
            if not fn.endswith(".jsonl"):
                continue
            day = fn[:-6]
            try:
                d = date.fromisoformat(day)
            except ValueError:
                kept += 1
                continue
            if d.toordinal() >= cutoff:
                kept += 1
                continue
            path = os.path.join(data_dir, fn)
            if day in archived:
                os.remove(path)
                continue
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        arch.write(line + "\n")
            os.remove(path)
            moved += 1
    return moved, kept


def consolidate_snapshots(keep_days=30, today=None):
    """Move tool snapshot files older than the retention window into the archive."""
    if today is None:
        today = date.today()
    return _consolidate(DATA_DIR, ARCHIVE_PATH, keep_days, today, "tool")


def consolidate_agents(keep_days=30, today=None):
    """Move agent snapshot files older than the retention window into the archive."""
    if today is None:
        today = date.today()
    return _consolidate(AGENT_DATA_DIR, AGENT_ARCHIVE_PATH, keep_days, today, "agent")


def load_runner_config():
    with open(RUNNER_CONFIG_PATH, "r") as f:
        return json.load(f)


def runner_snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(RUNNER_DATA_DIR, str(d) + ".jsonl")


def load_runner_snapshots():
    """Return {date_str: {runner_id: rec}} (archive + daily, daily wins)."""
    return _load_daily_files(RUNNER_DATA_DIR, "runner", _load_archive(RUNNER_ARCHIVE_PATH, "runner"))


def consolidate_runners(keep_days=30, today=None):
    """Move runner snapshot files older than the retention window into the archive."""
    if today is None:
        today = date.today()
    return _consolidate(RUNNER_DATA_DIR, RUNNER_ARCHIVE_PATH, keep_days, today, "runner")


def load_free_apps_config():
    with open(FREE_APPS_CONFIG_PATH, "r") as f:
        return json.load(f)


def free_app_snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(FREE_APPS_DATA_DIR, str(d) + ".jsonl")


def load_free_app_snapshots():
    """Return {date_str: {app_id: rec}} (archive + daily, daily wins)."""
    return _load_daily_files(FREE_APPS_DATA_DIR, "app", _load_archive(FREE_APPS_ARCHIVE_PATH, "app"))


def consolidate_free_apps(keep_days=30, today=None):
    """Move free-app snapshot files older than the retention window into the archive."""
    if today is None:
        today = date.today()
    return _consolidate(FREE_APPS_DATA_DIR, FREE_APPS_ARCHIVE_PATH, keep_days, today, "app")


LLM_CONFIG_PATH = os.path.join(ROOT, "config", "local-llm.json")
LLM_DATA_DIR = os.path.join(ROOT, "data", "local-llm_snapshots")
LLM_ARCHIVE_PATH = os.path.join(ROOT, "data", "archives", "local-llm_archive.jsonl")


def load_llm_config():
    with open(LLM_CONFIG_PATH, "r") as f:
        return json.load(f)


def llm_snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(LLM_DATA_DIR, str(d) + ".jsonl")


def load_llm_snapshots():
    """Return {date_str: {model_id: rec}} (archive + daily, daily wins)."""
    return _load_daily_files(LLM_DATA_DIR, "model", _load_archive(LLM_ARCHIVE_PATH, "model"))


def consolidate_llms(keep_days=30, today=None):
    """Move local-llm snapshot files older than the retention window into the archive."""
    if today is None:
        today = date.today()
    return _consolidate(LLM_DATA_DIR, LLM_ARCHIVE_PATH, keep_days, today, "model")
