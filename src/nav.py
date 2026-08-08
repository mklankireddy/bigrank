"""Shared navigation config + renderers for BigRank static pages.

All pages get their nav (and the landing page its section cards) from the single
NAV structure below. Each group is a small dropdown whose items are the pages.
Adding a future group (e.g. "Movies" -> English/Indian) means editing this one file.
"""
import os

LANDING_PAGE = "index.html"

NAV = [
    {
        "label": "Agents",
        "emoji": "🤖",
        "items": [
            {
                "key": "coding",
                "label": "Coding",
                "emoji": "💻",
                "page": "ai/agents/coding/index.html",
                "desc": "Cursor, Claude Code, Copilot, Windsurf & more",
            },
            {
                "key": "general",
                "label": "General-purpose",
                "emoji": "🧩",
                "page": "ai/agents/general/index.html",
                "desc": "OpenClaw, AutoGPT, Open Interpreter & more",
            },
        ],
    },
    {
        "label": "Apps",
        "emoji": "📱",
        "items": [
            {
                "key": "free-apps",
                "label": "Free Apps",
                "emoji": "🎁",
                "page": "ai/apps/free/index.html",
                "desc": "ChatGPT, Claude, Gemini, Copilot free tiers & more",
            },
        ],
    },
    {
        "label": "Models",
        "emoji": "🧠",
        "items": [
            {
                "key": "local-model-runner",
                "label": "Local Model Runner",
                "emoji": "🖥️",
                "page": "ai/model/local-model-runner/index.html",
                "desc": "Ollama, llama.cpp, vLLM & more",
            },
        ],
    },
]


def _rel_href(from_page, to_page):
    base = os.path.dirname(from_page) or os.curdir
    return os.path.relpath(to_page, base).replace("\\", "/")


def _item(active, from_page, item):
    emoji = f'<span class="i">{item["emoji"]}</span>' if item.get("emoji") else ""
    if item.get("disabled"):
        return (
            f'<a class="item disabled" title="{item.get("title", "")}">'
            f'{emoji}<span>{item["label"]}</span><span class="nsoon">soon</span></a>'
        )
    on = " on" if item["key"] == active else ""
    return (
        f'<a class="item{on}" href="{_rel_href(from_page, item["page"])}">'
        f'{emoji}<span>{item["label"]}</span><span class="arrow">→</span></a>'
    )


def render_nav(active, from_page):
    """Return the nav HTML for a page rendered at ``from_page`` (site-relative)."""
    brand = f'<div class="brand"><a href="{_rel_href(from_page, LANDING_PAGE)}">Big<span>Rank</span></a></div>'
    groups = []
    for group in NAV:
        items = "".join(_item(active, from_page, item) for item in group["items"])
        gemoji = f'{group["emoji"]} ' if group.get("emoji") else ""
        groups.append(
            '<div class="group">'
            f'<button class="gbtn" aria-haspopup="true">{gemoji}{group["label"]} <span class="caret">&#9662;</span></button>'
            '<div class="menu">' + items + "</div>"
            "</div>"
        )
    return '<nav class="nav">' + brand + '<div class="groups">' + "".join(groups) + "</div></nav>"


def render_cards():
    """Return landing-page section cards (hrefs are site-relative, so only valid from the root page)."""
    cards = []
    for group in NAV:
        items = []
        for item in group["items"]:
            if item.get("disabled"):
                items.append(
                    f'<div class="card-item disabled">'
                    f'<span class="itext"><span class="iname">{item["label"]}</span></span>'
                    f'<span class="soon">soon</span></div>'
                )
            else:
                desc = f'<span class="idesc">{item["desc"]}</span>' if item.get("desc") else ""
                items.append(
                    f'<a class="card-item" href="{item["page"]}">'
                    f'<span class="iemoji">{item["emoji"]}</span>'
                    f'<span class="itext"><span class="iname">{item["label"]}</span>{desc}</span>'
                    f'<span class="iarrow">→</span></a>'
                )
        head = f'<span class="che">{group["emoji"]}</span>{group["label"]}' if group.get("emoji") else group["label"]
        cards.append('<div class="card"><div class="card-head">' + head + "</div>" + "".join(items) + "</div>")
    return "".join(cards)
