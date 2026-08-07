"""Shared navigation config + renderers for BigRank static pages.

All pages get their nav (and the landing page its group cards) from the single
NAV structure below, so adding a future group (e.g. "Movies" -> English/Indian)
means editing this one file.
"""
import os

LANDING_PAGE = "index.html"

NAV = [
    {
        "label": "AI",
        "items": [
            {"key": "coding", "label": "Coding agents", "page": "ai/coding/index.html"},
            {"key": "general", "label": "General-purpose agents", "page": "ai/general/index.html"},
            {"key": "models", "label": "Models", "disabled": True, "title": "Coming soon"},
        ],
    },
]


def _rel_href(from_page, to_page):
    base = os.path.dirname(from_page) or os.curdir
    return os.path.relpath(to_page, base).replace("\\", "/")


def render_nav(active, from_page):
    """Return the nav HTML for a page rendered at ``from_page`` (site-relative)."""
    brand = f'<div class="brand"><a href="{_rel_href(from_page, LANDING_PAGE)}">Big<span>Rank</span></a></div>'
    groups = []
    for group in NAV:
        items = []
        for item in group["items"]:
            if item.get("disabled"):
                items.append(
                    f'<a class="item disabled" title="{item.get("title", "")}">{item["label"]}</a>'
                )
            else:
                on = " on" if item["key"] == active else ""
                items.append(
                    f'<a class="item{on}" href="{_rel_href(from_page, item["page"])}">{item["label"]}</a>'
                )
        groups.append(
            '<div class="group">'
            f'<button class="gbtn" aria-haspopup="true">{group["label"]} <span class="caret">&#9662;</span></button>'
            '<div class="menu">' + "".join(items) + "</div>"
            "</div>"
        )
    return '<nav class="nav">' + brand + '<div class="groups">' + "".join(groups) + "</div></nav>"


def render_cards():
    """Return landing-page group cards (hrefs are site-relative, so only valid from the root page)."""
    cards = []
    for group in NAV:
        items = []
        for item in group["items"]:
            if item.get("disabled"):
                items.append(
                    f'<div class="card-item disabled">{item["label"]} <span class="soon">soon</span></div>'
                )
            else:
                items.append(f'<a class="card-item" href="{item["page"]}">{item["label"]}</a>')
        cards.append('<div class="card"><h2>' + group["label"] + "</h2>" + "".join(items) + "</div>")
    return "".join(cards)
