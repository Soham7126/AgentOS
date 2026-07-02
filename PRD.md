# PRD: AgentOS

**Hackathon:** WeMakeDevs x Cognee Hackathon
**Track:** Best Use of Cognee Cloud
**Dates:** Jun 29 – Jul 5, 2026

---

## 1. Problem

Multi-agent coding workflows (Claude, Codex, Copilot working on the same codebase) currently rely on chat history to share context. This breaks down constantly:

- Context windows compact or reset, losing project history
- Handing a task from one agent to another means manually re-explaining the project
- No agent knows what another agent already decided, built, or is currently doing
- Architecture decisions ("why did we choose Redis?") live only in someone's memory or a buried Slack message

**Core insight:** agents don't need *more* context window — they need a shared, persistent, queryable memory that survives across sessions and across different agents entirely.

## 2. Solution

**AgentOS** is a CLI-based coordination layer for multi-agent coding teams, backed by **Cognee** as the shared knowledge graph. Instead of agents passing chat transcripts to each other, every task, decision, file, API, and bug becomes a node in a shared graph. Agents query that graph instead of being re-briefed by a human.

Cognee replaces "copy-paste the last 50 messages into the new agent's prompt" with a single command: `agent handoff codex`.

## 3. Goals (this hackathon)

| Goal | Success looks like |
|---|---|
| Demonstrate real multi-agent coordination | Claude, Codex, and Copilot (real or scripted) all contribute to one shared project graph |
| Use Cognee's full memory lifecycle | `remember()`, `recall()`, `improve()`, and `forget()` all appear meaningfully in the build, not just `remember`/`recall` |
| Ship a working CLI | All 6 commands run end-to-end against Cognee Cloud, not mocked |
| Tell a clear story | Judges understand the problem, the demo, and the impact within the first 60 seconds of watching |

## 4. Non-goals (explicitly out of scope for this build)

- Building a UI/dashboard (CLI only)
- Supporting agent frameworks beyond Claude Code, Codex, and (simulated) Copilot
- Real-time multi-user collaboration features
- Production-grade auth, multi-tenant isolation, or billing
- Supporting the other 8 Cognee integrations (LangGraph, ADK, n8n, Dify, etc.) — explicitly deferred to "future work" in the README

## 5. The demo project: RelayCLI

To make the graph contain real, varied, demo-able content, AgentOS coordinates the (real + scripted) build of **RelayCLI** — an open-source webhook relay CLI tool. See `architecture.md` for the task split across agents.

RelayCLI is the *subject matter*; AgentOS is *the product being submitted*. Don't confuse the two in any write-up — judges are evaluating AgentOS + Cognee usage, not RelayCLI's code quality.

## 6. Features (full detail in `features.md`)

1. Shared Project Knowledge Graph
2. Agent Workspace Memory
3. Agent Assignment
4. Intelligent Agent Handoff ← centerpiece, lead with this in demo
5. Multi-Agent Status Tracking
6. Timeline & Decision Memory (`agent why`)

Plus: explicit `improve()`/`forget()` lifecycle coverage (e.g. `agent forget <task>`).

## 7. Tech stack summary

- **CLI:** Node.js + TypeScript + Commander.js
- **Memory backend:** Cognee Cloud (`COGNEE-35` developer credit)
- **Cognee access:** Python bridge service (FastAPI) wrapping Cognee's SDK, called over HTTP from the Node CLI
- **Real agent integration:** Cognee's official `claude-code` plugin (lifecycle hooks) for Claude; scripted `remember()` calls via the bridge for Codex and Copilot
- **Demo subject:** RelayCLI (TypeScript CLI tool)

Full breakdown in `architecture.md`.

## 8. Judging criteria alignment

| Criterion | How AgentOS addresses it |
|---|---|
| Impact & Usefulness | Solves a real pain point (context loss in multi-agent dev) with daily-use potential beyond the hackathon |
| Creativity | Multi-agent *cross-session, cross-tool* handoff is a sharper angle than single-agent memory |
| Technical Excellence | Clean repo separation (CLI / bridge / integrations / demo-app), real Cognee Cloud usage, working tests |
| Best Use of Cognee | All four lifecycle methods used with clear purpose; both an official plugin (Claude) and direct SDK calls (Codex/Copilot) are demonstrated |
| User Experience | Single CLI, 6 clear commands, structured human-readable output (esp. `agent handoff`) |
| Presentation Quality | README + demo video walk through problem → solution → live handoff demo → impact |

## 9. Risks

| Risk | Mitigation |
|---|---|
| Node↔Python bridge adds integration overhead | Keep the bridge dead simple — 4 endpoints, no business logic, just pass-through to Cognee SDK |
| `agent handoff`'s structured recall returns inconsistent results | Pre-seed data carefully (see `seed_data.json`); test the exact demo query repeatedly before recording |
| Claude Code plugin's auto-tagging conflicts with our manual `agent:` tags | Decide reconciliation approach early — see open question in `architecture.md` |
| Running out of time before `improve()`/`forget()` are wired in | These are lowest priority if time runs short — everything else should work first |

## 10. Definition of done (hackathon submission)

- [ ] All 6 CLI commands run against live Cognee Cloud and return real data
- [ ] Seed data loaded, demo is reproducible from a clean Cognee project
- [ ] At least one `improve()` and one `forget()` call demonstrated
- [ ] README written with setup instructions, architecture diagram, and demo video link
- [ ] Demo video/live walkthrough recorded, ≤5 min, leads with `agent handoff`
- [ ] Submitted with Cognee Cloud track selected
