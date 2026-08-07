"""VS Code Marketplace installs/downloads via the Gallery extensionquery POST."""
import time

from common import TIMEOUT

URL = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"


def collect(session, tool):
    spec = tool.get("vscode")
    if not spec:
        return None
    ext_id = f"{spec['publisher']}.{spec['extension']}"

    payload = {
        "filters": [
            {
                "criteria": [{"filterType": 7, "value": ext_id}],
                "pageNumber": 1,
                "pageSize": 1,
            }
        ],
        "flags": 1938,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;api-version=3.0-preview.1",
    }

    for attempt in range(4):
        resp = session.post(URL, json=payload, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            body = resp.json()
            extensions = (body.get("results") or [{}])[0].get("extensions") or []
            if not extensions:
                return None
            ext = extensions[0]
            stats = {s["statisticName"]: s.get("value") for s in ext.get("statistics", [])}
            return {
                "installs": stats.get("install"),
                "downloads": stats.get("downloadCount"),
                "trending_weekly": stats.get("trendingweekly"),
                "trending_monthly": stats.get("trendingmonthly"),
                "released": ext.get("releaseDate"),
            }
        if resp.status_code in (403, 429):
            time.sleep(20 * (attempt + 1))
            continue
        resp.raise_for_status()
    raise RuntimeError("marketplace query failed after retries")
