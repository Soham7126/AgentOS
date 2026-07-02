# AgentOS Architecture

See the repo-root `ARCHITECTURE.md` for the full design doc. This file
records the decisions resolved *during* the build (ARCHITECTURE.md §6).

## Resolved: Claude plugin tag reconciliation (§2.3)

Decision: **(b) layer our own `agent:`/`type:` tags on top**, rather than
adapting queries to the plugin's native categories.

Reason: the bridge's `/remember` endpoint folds tags into the stored text
itself (`[agent=claude type=file ...]\n<content>`) before calling
`cognee.remember()`. This is under AgentOS's control regardless of whether
the write came from a manual `agent log` call or the Claude Code plugin's
auto-capture — so there's one consistent tagging convention across all
three agents, and `agent workspace <agent>` doesn't need agent-specific
query logic.

## Resolved: Codex integration

Scripted, per ARCHITECTURE.md §2.4 default. Codex's contributions are
written via `agent log --agent codex "..."` and the seed data, identically
to Copilot. No real tool-wrapper integration wired up — degrades
gracefully with zero feature loss, as anticipated.

## Resolved: Stripe bug lifecycle

The Stripe signature bug stays in seed data as an **open, unassigned bug**
so it has a natural demo moment in `agent handoff codex` (see FEATURES.md
§4 acceptance criteria — handoff must surface it). `agent forget` is
demonstrated separately, on a *completed* task (see `docs/demo-script.md`),
so the two features get independent demo moments instead of competing for
the same one.

## Known limitation: `/api/v1/improve` not exposed on this tenant

Verified live against the provisioned Cognee Cloud tenant: `remember`,
`recall`, and `forget` all work end-to-end (`/api/v1/remember`,
`/api/v1/recall`, `/api/v1/forget` all present per the tenant's
`/openapi.json`), but `/api/v1/improve` returns 404 — this tenant build
doesn't expose that route yet. The bridge's `/improve` endpoint catches
this and reports `{"status": "unavailable", ...}` instead of crashing.

This doesn't block the PRD's `improve()` lifecycle requirement: the
primary, demoable `improve()` coverage is the Claude Code plugin's
automatic `SessionEnd` hook (ARCHITECTURE.md §2.3), which is independent
of this REST route. Point to that explicitly in the README/demo rather
than the manual bridge endpoint.

## Verified live end-to-end (2026-07-02)

Ran `seed/seed_data.py` (21/21 entries) against the real tenant, then all
9 CLI commands against live data:

- `remember`/`recall`/`forget` confirmed working over `cognee.serve()`
  remote mode — note the SDK's remote-mode responses are **plain dicts**,
  not the `RememberResult`/`SearchResultItem` objects the local SDK path
  returns; the bridge must handle both shapes (see `bridge/main.py`).
- `agent handoff codex` stress-tested 3x — Current Task, Decisions,
  Dependencies, and the open Stripe bug all surfaced correctly every run.
- GRAPH_COMPLETION recall is occasionally non-deterministic on short
  factual queries (returns a conversational filler like "Got it,
  continuing..." instead of the fact) — a rerun typically self-corrects.
  Not fully eliminated; worth a retry-once wrapper if it recurs during
  the actual recording.
- `agent forget` resolves `target` → `data_id` via a `SearchType.CHUNKS`
  recall (chunk payloads carry the source `data_id` in metadata); trusting
  the top relevance-ranked hit works better than also requiring an exact
  substring match, since chunk boundaries can split the target sentence.
