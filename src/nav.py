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
    groups_html = '<div class="groups" id="groups">' + "".join(groups) + "</div>"
    burger = (
        '<button class="burger" aria-label="Menu" aria-expanded="false" '
        'aria-controls="groups" type="button">&#9776;</button>'
    )
    style = (
        "<style>"
        ".burger{display:none;background:transparent;border:1px solid transparent;"
        "color:var(--text);font-size:20px;line-height:1;padding:4px 10px;border-radius:8px;cursor:pointer}"
        ".burger:hover{background:var(--panel2);border-color:var(--border)}"
        "@media (max-width:768px){"
        ".burger{display:block}"
        ".nav .groups{display:none;position:absolute;top:100%;left:0;right:0;"
        "flex-direction:column;align-items:stretch;gap:2px;background:var(--panel);"
        "border-bottom:1px solid var(--border);padding:6px 12px 10px}"
        ".nav.open .groups{display:flex}"
        ".nav .groups .group{width:100%}"
        ".nav .groups .gbtn{width:100%;text-align:left}"
        ".nav .groups .menu{position:static;min-width:0;box-shadow:none;"
        "border:1px solid var(--border);margin:2px 0 6px}"
        ".nav .groups .menu a.item{padding:9px 12px}}"
        "</style>"
    )
    script = (
        "<script>(function(){"
        "var nav=document.querySelector('.nav'),b=nav&&nav.querySelector('.burger');"
        "if(!nav||!b)return;"
        "var close=function(){nav.classList.remove('open');b.setAttribute('aria-expanded','false')};"
        "b.addEventListener('click',function(e){e.stopPropagation();"
        "var open=nav.classList.toggle('open');b.setAttribute('aria-expanded',open?'true':'false')});"
        "document.addEventListener('click',function(e){if(!nav.contains(e.target))close()});"
        "document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});"
        "})();"
        "</script>"
    )
    return (
        '<nav class="nav">' + brand + burger + groups_html + "</nav>"
        + style + script
    )
