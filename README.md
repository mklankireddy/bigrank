# 🚀 BigRank — Daily AI Tool Rankings

Independent, daily-updated rankings of **80+ AI tools across five leaderboards**, scored by
**public usage signals** — not benchmarks or surveys. Every number is snapshotted, committed,
and auditable.

| Board | What it ranks | Live page |
|---|---|---|
| 💻 **Coding Agents** | Cursor, Claude Code, Copilot, Windsurf, Cline & more | [ai/agents/coding](https://mklankireddy.github.io/bigrank/ai/agents/coding/) |
| 🧩 **General-purpose Agents** | OpenClaw, AutoGPT, Open Interpreter & more | [ai/agents/general](https://mklankireddy.github.io/bigrank/ai/agents/general/) |
| 🎁 **Free AI Apps** | ChatGPT, Claude, Gemini free tiers & more | [ai/apps/free](https://mklankireddy.github.io/bigrank/ai/apps/free/) |
| 🖥️ **Local Model Runners** | Ollama, llama.cpp, vLLM, LM Studio & more | [ai/model/local-model-runner](https://mklankireddy.github.io/bigrank/ai/model/local-model-runner/) |
| 📦 **Local LLMs** | Llama, Qwen, Gemma, GPT-OSS — fit to your RAM/VRAM | [ai/model/local-llm](https://mklankireddy.github.io/bigrank/ai/model/local-llm/) |

## 🔄 How it works

1. 📥 **Collect (daily)** — a GitHub Actions workflow (`.github/workflows/collect.yml`, cron
   05:00 UTC) runs each board's collector and writes one JSONL snapshot per board:
   `data/<board>_snapshots/<date>.jsonl` (one line per entry).
2. ♻️ **Retain & archive** — snapshots are kept for the trailing **30 days**; older history is
   consolidated into `data/archives/<board>_archive.jsonl`, so the full history is committed to
   this repo and every number stays auditable.
3. 🏗️ **Build** — Python builders render a static page per board plus the landing page into `site/`.
4. 🚀 **Deploy** — GitHub Pages serves the static site.

## 🧮 Scoring

- Every metric is **min-max normalized** to 0–100 across tracked entries.
- Composites are weighted averages with the **full weight sum as the denominator**: missing
  sources count as zero, so an entry with data from only some sources is capped by the weight
  those sources carry (a **coverage penalty**). Rows with incomplete data show an
  `n/m sources` badge.
- Weights live in each board's config file and can also be tweaked **live on the page**
  (client-side recompute — no reload).
- Composite views per board: **Install base** + **Momentum** (coding agents, runners),
  **Free Tier Value** + **Momentum** (free apps), **Activity** + **Adoption** (general agents),
  a single **Capability** score (local LLMs).

## 💻 Coding Agents

Ranks AI coding agents — Cursor, Claude Code, GitHub Copilot, Windsurf, Codex, Devin, Aider,
Cline, Continue, Gemini CLI, Replit, OpenHands, Grok Build, Roo Code, Plandex — by public usage
signals. Tracked in `config/tools.json`.

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

Two composite views:

- **Install base** — cumulative reach: stars + VS Code installs + Open VSX + JetBrains +
  30d HN/Reddit mentions.
- **Momentum** — 30d velocity: stars gained + installs gained + commits + 7d HN/Reddit mentions.

## 🧩 General-purpose Agents

Ranks open-source general-purpose AI agents (OpenClaw, AutoGPT, Open Interpreter & more) on two
GitHub-centric composites. Tracked in `config/agents.json`.

- **Activity** — commits 30d (40) + issues opened 30d (30) + issues closed 30d (30)
- **Adoption** — stars (25) + forks 30d (20) + watchers (10) + 30d HN mentions (25) +
  30d Reddit mentions (20)

Each agent also carries hand-maintained, display-only fields — `category`, `setup`
instructions, an `effort` tag (`easy`/`medium`/`advanced`) and `pricing` — none of these affect
the score. A release-based freshness badge (Active / Steady / Slowing / Stale) summarizes
maintenance status.

## 🎁 Free AI Apps

Ranks everyday consumer AI apps — ChatGPT, Claude, Gemini, Copilot, Perplexity, Grok,
NotebookLM, Google AI Studio, Hugging Chat, Mistral Le Chat, DeepSeek, Meta AI — by how useful
they are on their **free tier**: what students and people who can't pay for frontier models can
actually use. Tracked in `config/free_apps.json`.

| Source | Metric | API |
|---|---|---|
| GitHub | stars + 30d star delta (only apps with an open-source repo) | `GET /repos/{owner}/{repo}` |
| Hacker News | mentions in trailing 7d / 30d | Algolia `hn.algolia.com/api/v1/search` |
| Reddit | mentions in trailing 7d / 30d (newest-first, capped at 1000) | OAuth `search.json` |
| Hand-maintained | free-tier / ease-of-access / usefulness ratings (0–100) + note | `config/free_apps.json` |

Two composite views (**Free Tier Value** and **Momentum**), same normalization +
coverage-penalty scoring as the other boards.

**Automated vs hand-maintained:** the daily snapshot only carries public signals — most of
these apps are closed-source, so the GitHub column is mostly empty *by design*. Three factors
(`free_tier`, `ease_of_access`, `usefulness`) are **human ratings** maintained in the config by
the maintainer: never snapshotted, always present (so they never trigger the coverage penalty),
marked <span class="tag hand">hand</span> in the table, and subjective by nature.

## 🖥️ Local Model Runners

Ranks local model runners and inference servers — Ollama, llama.cpp, vLLM, LM Studio, SGLang,
TensorRT-LLM, Hugging Face TGI, LocalAI, GPT4All, Tabby, OpenWebUI and more — under
**AI → Models → Local Model Runner**. Tracked in `config/local-model-runner.json`.

| Source | Metric | API |
|---|---|---|
| GitHub | stars, forks, commits pushed to the runner's repo, trailing 30d | `GET /repos/{owner}/{repo}` + commit search |
| Docker Hub | cumulative image pulls (official images only) | `hub.docker.com/v2/repositories/{ns}/{name}` |
| PyPI | monthly package downloads | `pypistats.org/api/packages/{pkg}/recent` |
| npm | monthly package downloads | `api.npmjs.org/downloads/point/last-month/{pkg}` |
| Hacker News | mentions in trailing 7d / 30d | Algolia `hn.algolia.com/api/v1/search` |
| Reddit | mentions in trailing 7d / 30d (newest-first, capped at 1000) | OAuth `search.json` |

Same **Install base** / **Momentum** scoring as the coding-agents board — runners without an
official Docker Hub image or package take a visible coverage penalty. Each runner also carries
hand-maintained, display-only tags (`ease`, `focus`, `type`) plus a `pricing` tag — none of
these affect the score.

## 📦 Local LLMs

Ranks open-weight LLMs people run locally — Llama 3.1/3.3, Qwen3/Qwen3.8, Gemma 3/4, Phi-4,
Mistral Small, DeepSeek-R1 distills, GLM-4, SmolLM3, GPT-OSS, Devstral, Mellum2, ZAYA1 and
more — under **AI → Models → Local LLMs**. Tracked in `config/local-llm.json`.

Unlike the other boards there are no public usage APIs for model downloads — every value is
**hand-maintained from official model cards**:

- parameters, license, GGUF quant formats, minimum RAM/VRAM (Q4-class approximations)
- MMLU/HumanEval benchmarks — or the closest published equivalents for newer models
  (hover a benchmark cell on the page for its exact source)
- context length, best use case
- a `last_benchmark_update` date shown as a freshness badge: 🟢 ≤90d · 🟡 ≤180d · 🔴 older

Models are ranked by a **Capability** composite (min-max normalized MMLU + HumanEval + context
length with client-adjustable weights), and two dropdowns filter models to what fits your
machine's RAM/VRAM budget.

> To add or correct a model, edit `config/local-llm.json` via a pull request — the daily
> collector only records which models are tracked.

## 🏷️ Pricing tags

Each tool/agent also carries a hand-maintained `pricing` tag in its config: `free`,
`freemium`, or `paid`. It is an **approximation, not a metric** — it never affects scoring.
Classification rule (based on the official pricing page):

- **free** — no payment required for the core product (may still need your own LLM/API key).
- **freemium** — a usable free tier exists, but the full value is tied to a paid plan.
- **paid** — a subscription/paid plan is required to use it at all.

Rule of thumb: open-source core with no official paid offering → `free`; open-source core plus
a paid cloud/hosted version → `freemium`; closed product with a paywall → `paid`. Update the
tag by editing the config; it appears next to the name on the ranking pages, with a legend
above each table.

## 📁 Project layout

```
config/tools.json          # tracked tools + repo/ext/plugin ids + search phrases + weights
config/agents.json         # tracked open-source agents + activity/adoption weights + setup notes
config/local-model-runner.json  # tracked local model runners + weights + display-only tags
config/free_apps.json      # tracked free AI apps + hand-maintained factors + weights
config/local-llm.json      # tracked local LLMs + hand-maintained specs/benchmarks + weights
src/
  collect.py               # runs all collectors -> data/coding-agents_snapshots/<date>.jsonl, then prunes old days
  collect_agents.py        # agent collectors -> data/general-purpose-agents_snapshots/<date>.jsonl
  collect_local_model_runner.py  # runner collectors -> data/local-model-runner_snapshots/<date>.jsonl
  collect_free_apps.py     # free-app collectors -> data/free-apps_snapshots/<date>.jsonl
  collect_local_llm.py     # config audit trail -> data/local-llm_snapshots/<date>.jsonl (no network)
  nav.py                   # single source of truth for the top nav (group -> sections -> items) + landing cards
  build_landing.py         # renders site/index.html (landing page)
  build_site.py            # renders site/ai/agents/coding/ (coding agents ranking)
  build_agents.py          # renders site/ai/agents/general/ (general-purpose agents ranking)
  build_local_model_runner.py  # renders site/ai/model/local-model-runner/ (local model runner ranking)
  build_free_apps.py       # renders site/ai/apps/free/ (free AI apps ranking)
  build_local_llm.py       # renders site/ai/model/local-llm/ (local LLM ranking)
  score.py                 # normalization + composites + time series
  common.py                # config load, HTTP, snapshot I/O, retention/archive
  sources/                 # github.py, github_agent.py, github_runner.py, hn.py, reddit.py, vscode.py, openvsx.py, jetbrains.py, docker.py, pypi.py, npm.py
  templates/index.html     # the coding agents ranking page
  templates/agents.html    # the general-purpose agents ranking page
  templates/local_model_runner.html  # the local model runner ranking page
  templates/free_apps.html # the free apps ranking page
  templates/local_llm.html # the local LLM ranking page
  templates/landing.html   # the landing page
data/<board>_snapshots/<date>.jsonl   # daily snapshots per board, trailing 30 days
data/archives/<board>_archive.jsonl   # consolidated history older than 30 days, per board
site/                      # generated static site (index.html, ai/agents/, ai/model/, ai/apps/)
.github/workflows/collect.yml
```

Boards: `coding-agents`, `general-purpose-agents`, `local-model-runner`, `free-apps`,
`local-llm`.

## 👀 Visitor features

The landing page's **Raw data & tool requests** section lets visitors:

- 🗂️ **Browse the snapshot archive** — links to each board's `data/*_snapshots/` folder in the
  repo (read-only; history is auditable).
- 📮 **Request a tool** — a small form (title, what needs to be ranked and how, official link)
  that opens a pre-filled GitHub issue. Visitors fill in three fields; the only extra step is
  clicking *Submit* on GitHub's page (login required), since a static site cannot create issues
  via the API. The matching issue form lives at
  `.github/ISSUE_TEMPLATE/tool_request.yml`. Only maintainers can change the `config/*.json`
  files, so tracked lists and scoring are never editable from the page.

The repo URL for those links comes from `GITHUB_REPOSITORY` in CI, or `meta.repo` in
`config/tools.json` for local previews.

## ⚠️ Caveats

- These are **relative signals**, not absolute usage or active-user counts. Marketplace
  "installs/downloads" are cumulative server-reported totals.
- Missing sources count as zero in the composite (coverage penalty); sparse-data entries rank lower.
- Commit-message search is noisy (AI-generated commits) and intentionally excluded from scores.
- Reddit counts cap at 1,000 newest results per entry per day (a `capped` flag is stored).
- A ranking is only as good as its data sources; each snapshot is committed so the methodology
  can always be audited and fixed.
