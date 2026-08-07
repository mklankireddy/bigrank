# AI Coding Agent Usage Rankings (Live)

An always-on ranking of AI coding agents — Cursor, Claude Code, GitHub Copilot, Windsurf,
Codex, Devin, Aider, Cline, Continue, Gemini CLI, Replit, OpenHands, Grok Build, Roo Code, Plandex — scored by **public
usage signals**, not benchmarks or surveys.

The collector runs **daily** via GitHub Actions, snapshots every source into
`data/snapshots/<date>.jsonl`, and deploys a static ranking page to GitHub Pages.
Daily snapshots are kept for the trailing **30 days**; older history is
consolidated into `data/archive.jsonl` (one line per tool-day) so the full
history is committed to this repo and every number is auditable.

Live page: [bigrank](https://<your-username>.github.io/bigrank/) (enable Pages, see below).

## Signals collected (per tool, per day)

| Source | Metric | API |
|---|---|---|
| GitHub | stars, forks, `pushed_at` | `GET /repos/{owner}/{repo}` |
| GitHub | commits pushed to own repo, trailing 30d | commit search `repo:… committer-date:>…` |
| GitHub | commit-message mentions (noisy, not in score) | commit search |
| Hacker News | mentions in trailing 7d / 30d | Algolia `hn.algolia.com/api/v1/search` |
| Reddit | mentions in trailing 7d / 30d (newest-first, capped at 1000) | OAuth `search.json` |
| VS Code Marketplace | installs, downloads, weekly trending | Gallery `extensionquery` POST |
| Open VSX | downloads | `open-vsx.org/api/{ns}/{name}` |
| JetBrains Marketplace | plugin downloads (official plugins only) | `plugins.jetbrains.com/api/plugins/{id}` |

Each metric is **min-max normalized** to 0–100 across tracked tools. Two composite views:

- **Install base** — cumulative reach: stars + VSCode installs + Open VSX + JetBrains + 30d HN/Reddit mentions.
- **Momentum** — 30d velocity: stars gained + installs gained + commits + 7d HN/Reddit mentions.

The composite is a weighted average with the **full weight sum as the denominator**: missing
sources count as zero, so a tool with data from only some sources is capped by the weight those
sources carry (a coverage penalty). Rows with incomplete data show an `n/m sources` badge.

Weights are in `config/tools.json` and can also be tweaked live on the page (client-side
recompute).

## Pricing tags

Each tool/agent also carries a hand-maintained `pricing` tag in `config/tools.json` /
`config/agents.json`: `free`, `freemium`, or `paid`. It is an **approximation, not a metric** —
it never affects scoring. Classification rule (based on the official pricing page):

- **free** — no payment required for the core product (may still need your own LLM/API key).
- **freemium** — a usable free tier exists, but the full value is tied to a paid plan.
- **paid** — a subscription/paid plan is required to use it at all.

Rough rule of thumb: open-source core with no official paid offering → `free`; open-source core
plus a paid cloud/hosted version → `freemium`; closed product with a paywall → `paid`. Update the
tag by editing the config; it appears next to the tool name on both ranking pages, with a legend
above each table.

## Project layout

```
config/tools.json          # tracked tools + repo/ext/plugin ids + search phrases + weights
config/agents.json         # tracked open-source agents + activity/adoption weights + setup notes
src/
  collect.py               # runs all collectors -> data/snapshots/<date>.jsonl, then prunes old days
  collect_agents.py        # agent collectors -> data/agent_snapshots/<date>.jsonl
  nav.py                   # single source of truth for the top nav groups + landing cards
  build_landing.py         # renders site/index.html (landing page)
  build_site.py            # renders site/ai/coding/ (AI coding agents ranking)
  build_agents.py          # renders site/ai/general/ (general-purpose agents ranking)
  score.py                 # normalization + composites + time series
  common.py                # config load, HTTP, snapshot I/O, retention/archive
  sources/                 # github.py, github_agent.py, hn.py, reddit.py, vscode.py, openvsx.py, jetbrains.py
  templates/index.html     # the AI coding agents ranking page
  templates/agents.html    # the general-purpose agents ranking page
  templates/landing.html   # the landing page
data/snapshots/<date>.jsonl  # daily tool snapshots, trailing 30 days
data/agent_snapshots/<date>.jsonl  # daily agent snapshots, trailing 30 days
data/archive.jsonl           # consolidated tool history older than 30 days
data/agents_archive.jsonl    # consolidated agent history older than 30 days
site/                      # generated static site (index.html, ai/coding/, ai/general/)
.github/workflows/collect.yml
```

## Visitors: snapshots & tool requests

The live page's **Raw data & tool requests** section lets visitors:

- **Browse/download snapshots** — each date is a link to that day's raw `.jsonl` in the repo
  (read-only; history is auditable).
- **Request a tool** — a button opens a pre-filled GitHub issue (see
  `.github/ISSUE_TEMPLATE/tool_request.yml`). Visitors can *request* additions; only maintainers
  can change `config/tools.json`, so the tracked list and scoring are never editable from the page.

The repo URL for those links is set automatically from `GITHUB_REPOSITORY` in CI, or via
`meta.repo` in `config/tools.json` for local previews.

## Run it locally

```bash
pip install -r requirements.txt
GITHUB_TOKEN=ghp_xxx python src/collect.py --dry-run   # collect for today, no files written
python src/collect.py --date 2026-08-07                # write today's snapshot
python src/build_landing.py                            # build landing page
python src/build_site.py                               # build site/ai/coding/
python src/build_agents.py                             # build site/ai/general/
python -m http.server -d site 8000                     # preview
```

Notes on local runs:

- GitHub is **rate-limited without a token** (search 10 req/min). The collectors pace
  themselves (~7s between search calls) so a full dry-run takes a few minutes. In CI the
  built-in `GITHUB_TOKEN` avoids this.
- Reddit is skipped unless `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` are set.

## One-time setup

1. **Enable GitHub Pages.** Repo → Settings → Pages → Source: **GitHub Actions**.

2. **Reddit credentials (optional but recommended).** Create a free "script" app at
   <https://www.reddit.com/prefs/apps> (type *script*, any redirect URI such as
   `http://localhost`). Copy the client id and secret, then add repo secrets:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`

3. **First run.** Either wait for the daily cron (05:00 UTC), or go to Actions →
   *collect-and-deploy* → **Run workflow**. Momentum/velocity values become meaningful
   after ~7–30 days of snapshots accumulate.

## Adding a tool

Edit `config/tools.json` and add an entry with the tool's GitHub repo, VS Code
`publisher.extension`, Open VSX `namespace/name`, JetBrains `plugin_id` (official only),
and the HN/Reddit search phrases. Ambiguous names (cursor, windsurf, cline, devin, aider,
continue) should use a disambiguating phrase such as `"cursor" ai`.

## Caveats

- These are **relative signals**, not absolute usage or active-user counts. Marketplace
  "installs/downloads" are cumulative server-reported totals.
- Missing sources count as zero in the composite (coverage penalty); sparse-data tools rank lower.
- Commit-message search is noisy (AI-generated commits) and intentionally excluded from
  the composite score.
- Reddit counts cap at 1,000 newest results per tool per day (`capped` flag is stored).
- A ranking is only as good as its data sources; each snapshot is committed so the
  methodology can always be audited and fixed.
