"""Shared navigation config + renderers for BigRank static pages.

All pages get their nav (and the landing page its section cards) from the single
NAV structure below. Each group has one or more *sections* (subgroups), and each
section has *items* (pages). Adding a future group (e.g. "Movies" -> English/Indian)
means editing this one file.
"""
import os

LANDING_PAGE = "index.html"

NAV = [
    {
        "label": "AI",
        "emoji": "🤖",
        "tagline": "Live rankings",
        "sections": [
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
        cols = []
        for section in group["sections"]:
            items = "".join(_item(active, from_page, item) for item in section["items"])
            head = f'{section["emoji"]} {section["label"]}' if section.get("emoji") else section["label"]
            cols.append(f'<div class="menu-col"><div class="menu-head">{head}</div>{items}</div>')
        gemoji = f'{group["emoji"]} ' if group.get("emoji") else ""
        title = f'<div class="menu-title"><span class="i">{group["emoji"]}</span><div><b>{group["label"]}</b>'
        if group.get("tagline"):
            title += f'<span>{group["tagline"]}</span>'
        title += "</div></div>"
        groups.append(
            '<div class="group">'
            f'<button class="gbtn" aria-haspopup="true">{gemoji}{group["label"]} <span class="caret">&#9662;</span></button>'
            '<div class="menu mega">' + title + "".join(cols) + "</div>"
            "</div>"
        )
    return '<nav class="nav">' + brand + '<div class="groups">' + "".join(groups) + "</div></nav>"


def render_cards():
    """Return landing-page section cards (hrefs are site-relative, so only valid from the root page)."""
    cards = []
    for group in NAV:
        for section in group["sections"]:
            items = []
            for item in section["items"]:
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
            head = f'<span class="che">{section["emoji"]}</span>{section["label"]}' if section.get("emoji") else section["label"]
            cards.append('<div class="card"><div class="card-head">' + head + "</div>" + "".join(items) + "</div>")
    return "".join(cards)
