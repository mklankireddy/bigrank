"""Render site/index.html (the landing page) from the shared nav config."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT, SITE_DIR, VERSION, load_config, short_commit  # noqa: E402
from nav import render_cards, render_nav  # noqa: E402

TEMPLATE = os.path.join(ROOT, "src", "templates", "landing.html")


def main():
    cfg = load_config()
    repo = os.environ.get("GITHUB_REPOSITORY") or cfg["meta"].get("repo", "")
    archive = f"https://github.com/{repo}/tree/main/data" if repo else "#"

    with open(TEMPLATE) as f:
        html = f.read()
    html = html.replace("{{NAV}}", render_nav(active=None, from_page="index.html"))
    html = html.replace("{{CARDS}}", render_cards())
    html = html.replace("{{ARCHIVE_LINK}}", archive)
    html = html.replace("{{REPO}}", json.dumps(repo))
    html = html.replace("{{VERSION}}", VERSION)
    html = html.replace("{{COMMIT}}", short_commit() or "")
    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, "index.html"), "w") as f:
        f.write(html)
    print("built landing page -> site/index.html")


if __name__ == "__main__":
    main()
