# AgentOS

A CLI coordination layer for multi-agent coding teams, backed by
**Cognee Cloud** as a shared knowledge graph.

## Problem

Multi-agent coding workflows (Claude, Codex, Copilot on the same codebase)
rely on chat history to share context. Context windows compact, tasks get
handed off by pasting the last 50 messages, and decisions ("why did we
choose Redis?") live only in someone's memory. Agents don't need more
context window — they need a shared, persistent, queryable memory that
survives across sessions and across tools.

## Solution

Every task, decision, file, API, and bug becomes a node in one shared
Cognee graph. Agents query that graph instead of being re-briefed by a
human. `agent handoff codex` replaces "copy-paste the last 50 messages."

```
   Claude Code (plugin-hooked) ──────► Cognee Cloud  (direct, automatic)
                                              ▲
   Codex (scripted remember() calls) ────────┤
                                              ▲
   Copilot (scripted) ──────► AgentOS ───────┘

   agent assign / handoff / why / status / workspace / timeline / forget
                    │
                    ▼
            AgentOS CLI (Node/TS)
                    │
                    ▼
          Bridge service (Python/FastAPI)
                    │
                    ▼
              Cognee Cloud
        (remember / recall / improve / forget)
```


## Repo layout

| Path | What |
|---|---|
| `cli/` | Node.js + TypeScript + Commander.js CLI (the product) |
| `bridge/` | Python + FastAPI service — the only thing that imports the Cognee SDK |
| `seed/` | Seed script loading the RelayCLI demo dataset |
| `integrations/` | Cognee's `claude-code` and `codex` integrations |
| `demo-app/` | RelayCLI — the fictional webhook relay tool agents "build" (demo subject, not the submission) |
| `docs/` | Architecture decisions, demo script, judging checklist |
| `scripts/` | `setup.sh`, `demo.sh` |

## Setup

```bash
cp .env.example .env   # fill in COGNEE_API_KEY, COGNEE_SERVICE_URL, LLM_API_KEY
bash scripts/setup.sh   # installs deps, starts the bridge, seeds demo data
```

## Commands

```bash
agent assign <task> <agent>     # remember() — assign work
agent assigned <agent>          # recall()   — what is X working on
agent handoff <agent>           # recall()   — structured context package (centerpiece)
agent status                    # recall()   — all agents at a glance
agent workspace <agent>         # recall()   — one agent's files/tasks/decisions
agent timeline                  # recall()   — chronological history
agent why <decision>            # recall()   — targeted decision lookup
agent log <message>             # remember() — manual entry (Codex/Copilot activity)
agent forget <task>             # forget()   — prune a resolved task or bug
agent improve                   # improve()  — manually trigger graph enrichment
```

## Demo

```bash
bash scripts/demo.sh
```

See [docs/demo-script.md](docs/demo-script.md) for the narrated walkthrough
(≤5 min, leads with `agent handoff`). Demo video: _link here_.

## What this is not

CLI only (no dashboard), Claude Code + Codex integrations only (no
LangGraph/ADK/n8n/etc.), single project graph, no multi-tenant auth. See
[PRD.md](PRD.md) §4 for the full non-goals list.
