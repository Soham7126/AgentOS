# Tasks: AgentOS — 3-Day Build Plan

Companion to `PRD.md`, `ARCHITECTURE.md`, `FEATURES.md`. Tasks are ordered by dependency — earlier tasks unblock later ones. Each task has an owner type (you / Claude Code), a rough time estimate, and the acceptance check from `FEATURES.md` it satisfies.

This plan assumes the 7-day hackathon window but compresses the *build* into 3 focused days, leaving the remaining days for buffer, real-agent sessions, demo recording, and submission polish (see "After Day 3" at the bottom).

---

## Day 1 — Foundation: bridge, seed data, first real Cognee calls

**Goal by end of day:** Cognee Cloud is reachable, seed data is loaded, and you can `recall()` something real from the command line — even with zero CLI polish.

| # | Task | Owner | Est. | Resolves |
|---|---|---|---|---|
| 1.1 | Sign up for Cognee Cloud, redeem `COGNEE-35`, get API key + service URL | You | 15 min | — |
| 1.2 | Repo scaffold: create full folder structure from `architecture.md` §5 (empty dirs + placeholder files) | Claude Code | 20 min | — |
| 1.3 | `bridge/`: FastAPI skeleton with 4 endpoints (`/remember`, `/recall`, `/improve`, `/forget`) — stub logic first, just routing | Claude Code | 45 min | — |
| 1.4 | `bridge/`: wire real Cognee SDK calls into all 4 endpoints | Claude Code | 1 hr | Feature 1 (foundation) |
| 1.5 | `bridge/`: auto-stamp `created_at` on every `/remember` call (don't rely on caller to pass it) | Claude Code | 20 min | Feature 6 acceptance: consistent timestamping |
| 1.6 | Test bridge manually with `curl` — remember 2-3 facts, recall them back | You | 20 min | Feature 1 acceptance |
| 1.7 | Write `seed/seed_data.py` covering all 7 categories from the RelayCLI dataset (project facts, decisions, tasks, files, APIs, bugs, dependencies) | Claude Code | 1 hr | Feature 1 acceptance: all seed categories present |
| 1.8 | Run seed script against live Cognee Cloud, spot-check a few recalls manually | You | 20 min | Feature 1 acceptance |
| 1.9 | Install Cognee `claude-code` plugin (`claude --plugin-dir`), set env vars | You | 15 min | Architecture §2.3 |
| 1.10 | Run one real, throwaway Claude Code session with the plugin on — touch a couple of files, then inspect what got written to Cognee | You + Claude Code | 30 min | **Resolves the open tagging question** — see 1.11 |
| 1.11 | Decide: reuse plugin's native tags vs. layer custom `agent: claude` tag. Document the decision in `architecture.md` | You | 15 min | Feature 2 (unblocks Day 2 build) |

**Day 1 checkpoint:** bridge works, seed data is in Cognee, you know exactly how Claude's plugin tags its data. If 1.10/1.11 slips, everything downstream involving Claude's workspace tagging is at risk — don't skip it.

---

## Day 2 — CLI commands: assignment, status, workspace, handoff

**Goal by end of day:** All 6 CLI commands exist and return real data from Cognee. This is the biggest day — handoff is the priority if anything has to slip.

| # | Task | Owner | Est. | Resolves |
|---|---|---|---|---|
| 2.1 | `cli/`: Commander.js scaffold, `index.ts` registers stub subcommands for all 6 + `log` + `forget` | Claude Code | 30 min | — |
| 2.2 | `cli/`: `cogneeClient.ts` — thin HTTP wrapper calling the bridge's 4 endpoints | Claude Code | 30 min | — |
| 2.3 | `agent log <message>` — simplest command, manual `remember()` entry point for Codex/Copilot | Claude Code | 20 min | Enables scripting Codex/Copilot activity for rest of day |
| 2.4 | `agent assign <task> <agent>` | Claude Code | 30 min | Feature 3 |
| 2.5 | `agent assigned <agent>` | Claude Code | 30 min | Feature 3 acceptance |
| 2.6 | Test 2.4/2.5 end-to-end for all 3 agents | You | 20 min | Feature 3 acceptance: works for all 3 agents unchanged |
| 2.7 | `agent status` — recall across all agents in one call | Claude Code | 45 min | Feature 5 |
| 2.8 | Test 2.7, confirm it reflects a change made via `agent assign` immediately | You | 15 min | Feature 5 acceptance |
| 2.9 | `agent workspace <agent>` — apply the tagging decision from 1.11 | Claude Code | 1 hr | Feature 2 |
| 2.10 | Test 2.9 specifically for `claude` (real plugin data) vs. `codex`/`copilot` (scripted) — confirm no cross-contamination | You | 30 min | Feature 2 acceptance |
| 2.11 | **`agent handoff <agent>`** — break into 4 internal recall calls (task / decisions / deps / bugs) per the mitigation in `features.md`, then assemble | Claude Code | 1.5 hr | Feature 4 — centerpiece |
| 2.12 | Format `agent handoff` output to match the boxed example in `features.md` | Claude Code | 30 min | Feature 4 acceptance: clean human-readable output |
| 2.13 | Stress-test `agent handoff codex` repeatedly — confirm it reliably surfaces the Stripe bug + retry queue task + relevant decisions every run | You | 30 min | Feature 4 acceptance — **this is your highest-risk item, don't skip repeated testing** |

**Day 2 checkpoint:** if you're short on time, `agent handoff` (2.11–2.13) takes priority over polish on anything else — it's the feature judges will remember.

---

## Day 3 — Timeline, why, lifecycle coverage, real agent integration, polish

**Goal by end of day:** Full lifecycle coverage demonstrated, timeline/why working, and at least one real (non-Claude) agent contribution if time allows.

| # | Task | Owner | Est. | Resolves |
|---|---|---|---|---|
| 3.1 | `agent timeline` — chronological recall across all entries | Claude Code | 45 min | Feature 6 |
| 3.2 | `agent why <decision>` — targeted point lookup | Claude Code | 30 min | Feature 6 |
| 3.3 | Test `agent why` with a no-match keyword — confirm graceful "not found," no crash | You | 15 min | Feature 6 acceptance |
| 3.4 | Decide: does the Stripe bug get resolved + `forget()`'d in the demo, or stay open permanently? (Open decision from `features.md`) | You | 10 min | Unblocks 3.5 |
| 3.5 | `agent forget <task>` — wire to bridge's `/forget` endpoint | Claude Code | 30 min | Lifecycle coverage |
| 3.6 | Demo the full lifecycle: `agent assign` → work happens → `agent forget` → confirm via `agent status`/`timeline` that it's gone | You | 20 min | Lifecycle acceptance: clear before/after |
| 3.7 | Confirm Claude plugin's `SessionEnd` → `improve()` actually fired during Day 1's session; if not, manually trigger `improve()` via bridge and document where it's called | You | 20 min | Lifecycle acceptance: `improve()` demonstrated |
| 3.8 | **If time allows:** wire real Codex integration (`integrations/codex/`) instead of fully scripted — otherwise confirm scripted Codex data reads identically to real Claude data in `agent status`/`workspace` | You + Claude Code | 1–2 hr (optional) | Architecture §2.4 — graceful degradation if skipped |
| 3.9 | Full run-through: seed fresh → run all 6 commands in sequence → confirm nothing breaks | You | 30 min | All acceptance criteria, end-to-end |
| 3.10 | Write `README.md` — problem, solution, architecture diagram, setup steps, link to demo video | You + Claude Code | 1 hr | Presentation Quality criterion |
| 3.11 | Write `docs/demo-script.md` — exact command sequence for recording, leading with `agent handoff` | You | 30 min | Presentation Quality criterion |
| 3.12 | Record demo video (≤5 min) | You | 30–45 min | Submission requirement |
| 3.13 | Run through `docs/judging-checklist.md` against all 6 criteria before submitting | You | 20 min | Final QA |

**Day 3 checkpoint:** by end of day, the definition of done in `PRD.md` §10 should be fully checked off.

---

## After Day 3 (remaining hackathon days — buffer, not new scope)

Use any remaining days before the Jul 5 deadline for:
- Fixing whatever broke during the Day 3 full run-through
- A second, cleaner demo recording if the first one had hiccups
- Polishing README wording, adding screenshots of the Cognee Cloud dashboard (proves cloud usage for that judging track)
- **Do not add new features here** — scope is locked at the 6 features + lifecycle coverage from `features.md`. New scope this late is the most common way hackathon submissions end up half-broken.

---

## Critical path (if you only have time for one thing per day)

| Day | Non-negotiable minimum |
|---|---|
| 1 | Bridge works + seed data loaded (1.1–1.8) |
| 2 | `agent handoff` works reliably (2.11–2.13) — everything else on Day 2 can be rough if needed |
| 3 | One `forget()` + one `improve()` demonstrated, README written, demo recorded |
