# Features: AgentOS

Full detail for all 6 features plus lifecycle coverage. See `architecture.md` for system design and `prd.md` for project context.

---

## 1. Shared Project Knowledge Graph

**What it does:** The single source of truth all agents and all other features read from. Every task, decision, file, API, and bug lives here as a `remember()` call — nothing is stored as raw chat history.

**Cognee calls:** `remember()` only. No dedicated command — this is the substrate every other feature queries.

**Implementation notes:**
- Lives in `seed/seed_data.py` for initial load, plus ongoing writes from `agent assign`, `agent log`, and Claude's auto-captured activity.
- No filtering/tagging at this level — that's feature #2's job.

**Example call:**
```python
remember("RelayCLI uses Redis for the retry queue, TypeScript as the
implementation language, and Commander.js for CLI argument parsing.")
```

**Acceptance criteria:**
- [ ] Seed script runs cleanly against a fresh Cognee Cloud project
- [ ] All seed categories present: project facts, decisions, tasks, files, APIs, bugs, dependencies

---

## 2. Agent Workspace Memory

**What it does:** Each agent (Claude, Codex, Copilot) has memory tagged as theirs within the shared graph — not a separate store, just consistent attribution on every `remember()` call that agent's work produces.

**Cognee calls:** `remember()` with `agent` metadata tag · `recall()` filtered/scoped to that tag.

**CLI command:**
```bash
agent workspace claude
```

**Example output:**
```
Claude's Workspace
───────────────────
Owns: CLI + config layer

Created:
  - cli.ts (CLI entrypoint, Commander.js)
  - config.ts (config loader, Zod validation)

Tasks:
  - Build CLI entrypoint and config loader [in progress]
  - Write integration tests for relay pipeline [not started]

Decisions made:
  - Config schema in single relay.config.json, validated with Zod at startup
```

**Implementation notes:**
- ⚠ **Resolve before building:** Claude Code plugin auto-tags captured data with its own categories. Inspect actual plugin output before deciding whether to reuse its tags or layer a custom `agent: claude` tag on top. See `architecture.md` §2.3.
- For Codex/Copilot, tagging is straightforward since AgentOS writes those entries itself via `agent log`.

**Acceptance criteria:**
- [ ] `agent workspace claude` returns Claude's real captured files (from a real Claude Code session) correctly attributed
- [ ] `agent workspace codex` and `agent workspace copilot` return scripted data correctly attributed
- [ ] No cross-contamination between agents' workspaces in query results

---

## 3. Agent Assignment

**What it does:** Assigns a task to an agent and writes that assignment into the graph, so "what is X working on" is always answerable from memory.

**Cognee calls:** `remember()` on assignment · `recall()` on query.

**CLI commands:**
```bash
agent assign retry-queue codex
agent assigned codex
```

**Example output:**
```
$ agent assigned codex

Codex is assigned to:
  - Implement HMAC webhook signature validation [completed]
  - Implement Redis-backed retry queue with exponential backoff [in progress]
```

**Acceptance criteria:**
- [ ] `agent assign` writes a new task-assignment entry
- [ ] `agent assigned <agent>` correctly recalls only that agent's tasks, with status
- [ ] Works for all three agents without code changes per agent

---

## 4. Intelligent Agent Handoff ⭐ (centerpiece — lead with this in demo)

**What it does:** Generates a structured context package for an agent picking up work — current task, completed work, dependencies, open issues — replacing "paste the last 50 chat messages" with one command.

**Cognee calls:** `recall()` with a structured multi-part prompt (task state + dependencies + related decisions + open bugs).

**CLI command:**
```bash
agent handoff codex
```

**Example output:**
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

**Implementation notes:**
- This is the highest-risk feature for demo reliability — hybrid graph+vector recall needs to consistently return *all four* categories (task/decisions/deps/bugs), not just whichever matches best.
- Mitigation: test the exact demo query repeatedly against seeded data before recording; consider breaking this into 4 separate `recall()` calls internally (one per category) rather than one giant prompt, then assembling the output — more deterministic than hoping one query returns everything.
- Note in README: this is distinct from the Claude Code plugin's `PreCompact` hook, which preserves one agent's own context across compaction. `agent handoff` is cross-agent, not single-agent continuity.

**Acceptance criteria:**
- [ ] Returns accurate current task for the target agent
- [ ] Returns at least the 1-2 most relevant decisions
- [ ] Returns dependencies relevant to the current task
- [ ] Surfaces the open Stripe bug when handing off to Codex
- [ ] Output format is clean and human-readable, not raw JSON

---

## 5. Multi-Agent Status Tracking

**What it does:** Shows what every agent is doing right now, pulled live from the graph.

**Cognee calls:** `recall("status of all agents")` — traverses Agent → ASSIGNED_TO → Task across all three agents in one query.

**CLI command:**
```bash
agent status
```

**Example output:**
```
$ agent status

Claude
  Working on: Build CLI entrypoint and config loader [in progress]

Codex
  Working on: Implement Redis-backed retry queue [in progress]

Copilot
  Working on: Build email destination adapter [in progress]
```

**Acceptance criteria:**
- [ ] Returns current task for all three agents in one call
- [ ] Reflects updates immediately after `agent assign` changes something

---

## 6. Timeline & Decision Memory

**What it does:** Every meaningful event becomes a timestamped graph node, queryable as history. Any decision can be explained on demand.

**Cognee calls:** `remember()` on every event as it happens · `recall()` for chronological timeline and targeted "why" lookup.

**CLI commands:**
```bash
agent timeline
agent why redis
```

**Example output:**
```
$ agent timeline

Day 1
  Claude created config.ts
  Codex decided: HMAC-SHA256 for signature validation
  Codex completed: HMAC webhook signature validation
  Claude decided: single relay.config.json schema with Zod

Day 2
  Copilot decided: common Adapter interface for destinations
  Copilot completed: Slack destination adapter
  Codex reported bug: Stripe signature validation failing intermittently


$ agent why redis

Decision: Use Redis for the retry queue
Reason: In-memory retries are lost on process restart; webhook
        relays need durability across crashes
Decided by: Codex
Date: Day 1
```

**Implementation notes:**
- Requires consistent timestamping on every `remember()` call — easy to forget when writing seed data or scripted `agent log` entries. Enforce this in the bridge service (`/remember` endpoint auto-stamps `created_at` if not provided), not by convention alone.

**Acceptance criteria:**
- [ ] `agent timeline` returns events in correct chronological order across all agents
- [ ] `agent why <decision>` correctly recalls reason, decider, and date for a specific decision
- [ ] `agent why` handles a decision keyword that has no exact match gracefully (no crash, helpful "not found" message)

---

## Lifecycle coverage (cross-cutting, not a standalone feature)

| Stage | Where it's demonstrated |
|---|---|
| `remember()` | Every feature above |
| `recall()` | Every feature above |
| `improve()` | Claude Code plugin's automatic `SessionEnd` hook; optionally also triggered manually post-handoff |
| `forget()` | `agent forget <task>` — e.g. pruning a resolved task or closed bug |

**CLI command:**
```bash
agent forget stripe-bug-fix
```

**Open decision:** does the Stripe bug get resolved and `forget()`'d live in the demo (showing full lifecycle), or stay open permanently as the handoff hook? Resolve before finalizing the demo script — see `docs/demo-script.md`.

**Acceptance criteria:**
- [ ] At least one real `forget()` call demonstrated, with a clear before/after (`agent status` or `agent timeline` showing the entry gone)
- [ ] At least one `improve()` call demonstrated or explicitly called out in README (the automatic plugin one counts, but should be pointed to explicitly, not just implied)

---

## Out of scope for this build (do not implement)

- `agent context` (dynamic project summary) — redundant with `handoff` + `status`, cut to save time
- Per-agent dashboards/UI — CLI only
- Multi-project support — one project graph per hackathon demo
