import json
import os
import time
from datetime import date

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "tools.json")
DATA_DIR = os.path.join(ROOT, "data", "snapshots")
SITE_DIR = os.path.join(ROOT, "site")

USER_AGENT = "bigrank/0.1 (+https://github.com/" + os.environ.get("GITHUB_REPOSITORY", "bigrank") + ")"
TIMEOUT = 30


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


def snapshot_path(d=None):
    if d is None:
        d = date.today().isoformat()
    return os.path.join(DATA_DIR, str(d) + ".jsonl")


def load_snapshots():
    """Return {date_str: {tool_id: snapshot}} for every snapshot file present."""
    out = {}
    if not os.path.isdir(DATA_DIR):
        return out
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".jsonl"):
            continue
        day = fn[:-6]  # strip ".jsonl"
        out[day] = {}
        with open(os.path.join(DATA_DIR, fn)) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                out[day][rec["tool"]] = rec
    return out
