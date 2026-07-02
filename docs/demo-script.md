# Demo Script (≤5 min)

Run `scripts/demo.sh` for the exact sequence, or narrate manually:

1. **`agent handoff codex`** (centerpiece — lead with this)
   Shows the full context package Codex would need to pick up work:
   current task, relevant decisions, dependencies, and the open Stripe bug.
   This is the "replaces 50 pasted chat messages" moment.

2. **`agent status`**
   All three agents' current work, in one call.

3. **`agent workspace claude`**
   Claude's owned files/tasks/decisions — proves per-agent attribution
   works without per-agent code.

4. **`agent assigned codex`**
   Narrower slice of the same graph — Codex's task list with status.

5. **`agent timeline`**
   Full chronological history across all agents.

6. **`agent why redis`**
   Point lookup: decision, reason, decider — demonstrates targeted recall.

7. **`agent forget "HMAC webhook signature validation"`** → **`agent status`**
   Lifecycle close-out: forget a completed task, show it's gone from status.
   This plus the Claude Code plugin's automatic `SessionEnd` → `improve()`
   call (shown via bridge logs or the Cognee Cloud dashboard) covers all
   four lifecycle methods on camera.

## Before recording

- Run `python seed/seed_data.py` against a **fresh** Cognee project.
- Run `scripts/demo.sh` once through silently to confirm no command errors.
- Confirm `agent handoff codex` reliably returns all four sections
  (FEATURES.md's highest-risk acceptance criterion) — re-run 2-3 times.
