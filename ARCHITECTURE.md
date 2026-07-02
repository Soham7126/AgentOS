# Architecture: AgentOS

## 1. System overview

```
   Claude Code (real, plugin-hooked) ──────► Cognee Cloud  (direct, automatic)
                                                   ▲
   Codex (real, via scripted remember() calls) ────┤
                                                   ▲
   Copilot (scripted/simulated) ───────► AgentOS ──┘  (manual remember() calls)

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

**Key principle:** every agent's contribution ends up in the *same* Cognee graph, regardless of how it got there. Claude writes to it directly (via the official plugin's lifecycle hooks). Codex and Copilot's contributions are written on their behalf by AgentOS, since neither has a lifecycle-hook integration available.

## 2. Components

### 2.1 AgentOS CLI (`cli/`)

- **Stack:** Node.js, TypeScript, Commander.js
- **Role:** the user-facing surface. Every feature is a subcommand.
- **Talks to:** the bridge service, over local HTTP (e.g. `http://localhost:8000`)
- **Does NOT talk to Cognee directly** — all graph access goes through the bridge, so there's exactly one place that holds Cognee credentials and exactly one place that implements query logic.

Commands:

| Command | Cognee operation(s) |
|---|---|
| `agent assign <task> <agent>` | `remember()` |
| `agent assigned <agent>` | `recall()` |
| `agent handoff <agent>` | `recall()` — structured, multi-part |
| `agent status` | `recall()` — across all agents |
| `agent workspace <agent>` | `recall()` — scoped/tagged by agent |
| `agent timeline` | `recall()` — chronological |
| `agent why <decision>` | `recall()` — targeted lookup |
| `agent log <message>` | `remember()` — manual entry point for Codex/Copilot activity |
| `agent forget <task>` | `forget()` |

### 2.2 Bridge service (`bridge/`)

- **Stack:** Python, FastAPI
- **Role:** the only thing that imports Cognee's SDK and holds `COGNEE_API_KEY`. Exposes a thin REST API:
  - `POST /remember` — body: `{ content: string, tags?: object }`
  - `POST /recall` — body: `{ query: string, filters?: object }`
  - `POST /improve` — body: `{ session_id?: string }` (or whatever scope Cognee's `improve()` takes)
  - `POST /forget` — body: `{ target: string }`
- **Why a separate service instead of calling Cognee directly from Node:** Cognee's primary, most complete SDK is Python. Rather than fight an unofficial/partial Node client, isolate all Python-side complexity into one small service with a stable, boring HTTP contract.

### 2.3 Claude Code plugin (`integrations/claude-code/`)

- Cloned from `topoteretes/cognee-integrations`, installed via:
  ```bash
  claude --plugin-dir ./integrations/claude-code
  ```
- Hooks used: `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `PreCompact`, `SessionEnd`
- **What it gives us for free:**
  - Every file Claude creates/edits is automatically captured (`PostToolUse`) — no manual `remember()` needed for Claude's contributions
  - `SessionEnd` calls `cognee.improve()` automatically — this is our `improve()` lifecycle coverage for Claude's work
  - `PreCompact` builds a memory anchor before context compaction — a single-agent analog to our cross-agent `handoff`, worth noting in the README as "related but distinct"
- **Open question (resolve before building feature #2):** the plugin tags captured data with its own internal categories. AgentOS's "workspace memory" feature assumes we control the `agent:` tag ourselves. Before building `agent workspace claude`, inspect what the plugin actually writes (run one real Claude Code session with it on, then query Cognee directly) and decide:
  - (a) adapt our `recall()` query for Claude to use the plugin's native categories, or
  - (b) add our own `agent: claude` tag on top via a thin wrapper, if the plugin allows custom metadata injection

### 2.4 Codex integration (`integrations/codex/`)

- Cloned from `topoteretes/cognee-integrations`
- Unlike `claude-code`, this is **not** a lifecycle-hook plugin — it's a tool wrapper exposing Cognee as callable tools.
- For hackathon purposes, treat Codex's contributions as **scripted**: write `remember()` calls via `agent log` on Codex's behalf, the same way Copilot is handled. If time permits, wire the real tool integration; if not, this degrades gracefully with zero feature loss.

### 2.5 Seed data (`seed/`)

- `seed_data.py` — loads the full RelayCLI dataset (tasks, decisions, files, APIs, bugs, dependencies) into Cognee Cloud via the bridge, tagged by agent.
- Run once before any demo, and again before the final recorded demo to guarantee a clean, reproducible state.
- **Important:** seed data should be loaded *before* turning on the Claude Code plugin for any real build session, so RelayCLI's fictional project content doesn't get mixed up with AgentOS's own real build activity in the timeline.

### 2.6 Demo app (`demo-app/`) — RelayCLI

- The fictional/real webhook relay CLI tool the three agents are "building." See `PRD.md` §5.
- Task split:

| Agent | Owns | Files |
|---|---|---|
| Claude | CLI + config layer | `cli.ts`, `config.ts` |
| Codex | Validation + retry/queue | `validateSignature.ts`, `retryQueue.ts` |
| Copilot | Destination adapters | `adapters/slack.ts`, `adapters/email.ts` |

## 3. Data model (what gets `remember()`'d)

Every entry is natural-language text (Cognee handles extraction/graph-building internally), optionally tagged with metadata:

| Entity type | Example | Tags |
|---|---|---|
| Project fact | "RelayCLI uses Redis for the retry queue..." | none (shared root) |
| Decision | "Use Redis instead of in-memory array. Reason: ..." | `agent: codex`, `type: decision` |
| Task | "Build CLI entrypoint. Assigned to Claude. Status: in progress." | `agent: claude`, `type: task` |
| File | "File created: cli.ts. Created by Claude." | `agent: claude`, `type: file` |
| API | "API: POST /webhooks/:source. Receives..." | `type: api` |
| Bug | "Bug: Stripe signature validation failing..." | `type: bug`, `status: open` |
| Dependency | "RelayCLI depends on: ioredis, zod, ..." | `type: dependency` |

Tagging by `type` (not just `agent`) is what makes `agent why` (decisions only) and `agent timeline` (everything, chronological) behave differently from the same underlying graph.

## 4. Lifecycle coverage map

| Stage | Where it's used |
|---|---|
| `remember()` | Seed data load, `agent assign`, `agent log`, Claude's auto-captured files (via plugin) |
| `recall()` | `agent assigned`, `agent handoff`, `agent status`, `agent workspace`, `agent timeline`, `agent why` |
| `improve()` | Claude Code plugin's `SessionEnd` hook (automatic) + optionally triggered manually after a handoff |
| `forget()` | `agent forget <task>` — e.g. pruning a resolved bug or completed task |

## 5. Repo layout

See the folder structure already shared in chat — `cli/`, `bridge/`, `seed/`, `integrations/`, `demo-app/`, `docs/`, `scripts/` at the repo root.

## 6. Open decisions to make before/during build

1. **Claude plugin tag reconciliation** (§2.3) — resolve this first, it affects feature #2's implementation.
2. **Codex: real tool integration or fully scripted?** — default to scripted; upgrade only if time allows.
3. **Stripe bug lifecycle:** does it get resolved + `forget()`'d mid-demo, or stay open as a permanent handoff hook? Affects whether `agent forget` has a natural demo moment or needs a separate contrived example.
