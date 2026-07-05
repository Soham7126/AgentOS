# AgentOS

A CLI coordination layer for multi-agent coding teams, backed by
**Cognee Cloud** as a shared knowledge graph.

> Built for the [WeMakeDevs × Cognee Hackathon](https://www.wemakedevs.org/hackathons/cognee) — **Best Use of Cognee Cloud** track.

---

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

---

## Demo

> Watch the 5-minute walkthrough: **[YouTube / Loom link here]**

The demo runs AgentOS against a real Cognee Cloud tenant coordinating three
agents building **RelayCLI** — a webhook relay CLI tool. The graph contains
21 seeded entries across 7 categories (tasks, decisions, files, APIs, bugs,
dependencies, project facts).

### What `agent handoff codex` actually returns (live, not mocked)

```
═══════════════════════════════════
HANDOFF CONTEXT → Codex
═══════════════════════════════════

Current Task:
  Implement Redis-backed retry queue with exponential backoff
  Status: in progress

Relevant Decisions:
  - Redis chosen over in-memory array (durability across crashes)
  - HMAC-SHA256 chosen for signature validation (timing-attack safe,
    matches Stripe/GitHub standard)

Dependencies:
  ioredis, zod

Open Issues:
  ⚠ Stripe webhook signature validation failing intermittently.
    Suspected cause: 5-second timestamp tolerance too strict under
    network latency. Status: open, unassigned.

═══════════════════════════════════
```

No chat history transferred. No human re-briefing. One command.

---

## How Cognee is used

AgentOS uses all four stages of Cognee's memory lifecycle:

| Stage | Where |
|---|---|
| `remember()` | `agent assign`, `agent log`, Claude Code plugin's automatic `PostToolUse` capture |
| `recall()` | Every read command — `handoff`, `status`, `workspace`, `timeline`, `why`, `assigned` |
| `improve()` | `agent improve` (manual trigger) + Claude Code plugin's automatic `SessionEnd` hook |
| `forget()` | `agent forget` — prunes resolved tasks and closed bugs from the active graph |

The bridge service is the **only** component that imports the Cognee SDK.
The CLI talks to the bridge over HTTP — one place holds credentials, one
place holds query logic.

`agent handoff` deliberately uses four separate `recall()` calls (task /
decisions / dependencies / bugs) rather than one large prompt — more
deterministic, consistently surfaces all four categories across repeated runs.

---

## Repo layout

| Path | What |
|---|---|
| `cli/` | Node.js + TypeScript + Commander.js CLI (the product) |
| `bridge/` | Python + FastAPI service — the only thing that imports the Cognee SDK |
| `seed/` | Seed script loading the RelayCLI demo dataset (21 entries, 7 categories) |
| `integrations/` | Cognee's `claude-code` and `codex` integrations |
| `demo-app/` | RelayCLI — the fictional webhook relay tool agents "build" (demo subject, not the submission) |
| `docs/` | Architecture decisions, demo script, judging checklist |
| `scripts/` | `setup.sh`, `demo.sh` |

---

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- A [Cognee Cloud](https://platform.cognee.ai) account (use code `COGNEE-35` for developer access)
- An OpenAI or Anthropic API key (for Cognee's LLM calls)

### Install and run

```bash
cp .env.example .env
# Fill in:
#   COGNEE_API_KEY     — from Cognee Cloud dashboard → API Keys
#   COGNEE_SERVICE_URL — your tenant URL e.g. https://tenant-xxx.aws.cognee.ai
#   LLM_API_KEY        — your OpenAI or Anthropic key

bash scripts/setup.sh   # installs deps, starts the bridge, seeds demo data
```

### Install the Claude Code plugin (optional, for real Claude sessions)

```bash
claude plugin marketplace add topoteretes/cognee-integrations
claude plugin install cognee-memory@cognee
# Then set COGNEE_SERVICE_URL and COGNEE_API_KEY as env vars before launching claude
```

---

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

---

## The demo project: RelayCLI

To give the graph real, varied content, AgentOS coordinates three agents
building **RelayCLI** — an open-source webhook relay CLI that receives
webhooks, validates payloads, and forwards them to Slack, email, or a queue
with automatic retry on failure.

| Agent | Owns | Files |
|---|---|---|
| Claude | CLI + config layer | `cli.ts`, `config.ts` |
| Codex | Validation + retry queue | `validateSignature.ts`, `retryQueue.ts` |
| Copilot | Destination adapters | `adapters/slack.ts`, `adapters/email.ts` |

The 21 seeded graph entries cover: project facts, architecture decisions
(why Redis, why HMAC-SHA256, why the Adapter interface), task assignments
with status, files created per agent, APIs defined, open bugs (the Stripe
signature timing issue), and dependencies. This is what `agent handoff`,
`agent why`, and `agent timeline` query against.

**RelayCLI is the demo subject. AgentOS is the submission.**

---

## Key design decisions

**Why a separate bridge service instead of calling Cognee from Node?**
Cognee's primary SDK is Python. Rather than fight a partial Node client,
all SDK access is isolated in one small FastAPI service with a stable HTTP
contract. The CLI never holds credentials.

**Why four `recall()` calls in `agent handoff` instead of one?**
A single large prompt returns whichever category matches best, not all four
reliably. Splitting into task / decisions / dependencies / bugs and
assembling the output is more deterministic across repeated runs — critical
for a live demo.

**Why `agent handoff` over the Claude Code plugin's `PreCompact` hook?**
`PreCompact` preserves one agent's context across its own context window
reset. `agent handoff` is cross-agent — handing off between Claude, Codex,
and Copilot. Different problem, different solution, same underlying graph.

---

## Tech stack

| Layer | Choice |
|---|---|
| CLI | Node.js, TypeScript, Commander.js |
| Bridge | Python, FastAPI, Cognee SDK |
| Memory backend | Cognee Cloud |
| Claude integration | Cognee `claude-code` plugin (lifecycle hooks) |
| Demo subject | RelayCLI (TypeScript webhook relay CLI) |

---

## Built with

- [Cognee](https://github.com/topoteretes/cognee) — open-source AI memory platform
- [Cognee Cloud](https://platform.cognee.ai) — managed deployment
- [WeMakeDevs × Cognee Hackathon](https://www.wemakedevs.org/hackathons/cognee)