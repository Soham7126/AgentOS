"""Load the RelayCLI demo dataset into Cognee via the bridge.

Covers all 7 categories from ARCHITECTURE.md §3: project facts, decisions,
tasks, files, APIs, bugs, dependencies. Run against a fresh Cognee project
before any demo (see TASKS.md 1.7/1.8 and 3.9).
"""

import sys
import time

import requests

BRIDGE_URL = "http://localhost:8000"

ENTRIES: list[dict] = [
    # --- Project facts (no tags — shared root) ---
    {
        "content": (
            "RelayCLI is an open-source webhook relay CLI tool. It uses Redis for "
            "the retry queue, TypeScript as the implementation language, and "
            "Commander.js for CLI argument parsing."
        ),
        "tags": {"type": "fact"},
    },
    {
        "content": "RelayCLI's task split: Claude owns the CLI + config layer, Codex owns validation + retry/queue, Copilot owns destination adapters.",
        "tags": {"type": "fact"},
    },
    # --- Decisions ---
    {
        "content": (
            "Decision: Use Redis instead of an in-memory array for the retry queue. "
            "Reason: in-memory retries are lost on process restart; webhook relays "
            "need durability across crashes."
        ),
        "tags": {"agent": "codex", "type": "decision"},
    },
    {
        "content": (
            "Decision: Use HMAC-SHA256 for webhook signature validation. Reason: "
            "timing-attack safe, and matches the Stripe/GitHub signing standard."
        ),
        "tags": {"agent": "codex", "type": "decision"},
    },
    {
        "content": (
            "Decision: Config schema lives in a single relay.config.json file, "
            "validated with Zod at startup. Reason: one source of truth, fail fast "
            "on bad config."
        ),
        "tags": {"agent": "claude", "type": "decision"},
    },
    {
        "content": (
            "Decision: Use a common Adapter interface for all destinations (Slack, "
            "email, etc). Reason: keeps adding new destinations a matter of "
            "implementing one interface, not touching relay core."
        ),
        "tags": {"agent": "copilot", "type": "decision"},
    },
    # --- Tasks ---
    {
        "content": "Task: Build CLI entrypoint and config loader. Assigned to Claude. Status: in progress.",
        "tags": {"agent": "claude", "type": "task", "status": "in_progress"},
    },
    {
        "content": "Task: Write integration tests for relay pipeline. Assigned to Claude. Status: not started.",
        "tags": {"agent": "claude", "type": "task", "status": "not_started"},
    },
    {
        "content": "Task: Implement HMAC webhook signature validation. Assigned to Codex. Status: completed.",
        "tags": {"agent": "codex", "type": "task", "status": "completed"},
    },
    {
        "content": "Task: Implement Redis-backed retry queue with exponential backoff. Assigned to Codex. Status: in progress.",
        "tags": {"agent": "codex", "type": "task", "status": "in_progress"},
    },
    {
        "content": "Task: Build Slack destination adapter. Assigned to Copilot. Status: completed.",
        "tags": {"agent": "copilot", "type": "task", "status": "completed"},
    },
    {
        "content": "Task: Build email destination adapter. Assigned to Copilot. Status: in progress.",
        "tags": {"agent": "copilot", "type": "task", "status": "in_progress"},
    },
    # --- Files ---
    {
        "content": "File created: cli.ts (CLI entrypoint, Commander.js). Created by Claude.",
        "tags": {"agent": "claude", "type": "file"},
    },
    {
        "content": "File created: config.ts (config loader, Zod validation). Created by Claude.",
        "tags": {"agent": "claude", "type": "file"},
    },
    {
        "content": "File created: validateSignature.ts (HMAC-SHA256 webhook signature validation). Created by Codex.",
        "tags": {"agent": "codex", "type": "file"},
    },
    {
        "content": "File created: retryQueue.ts (Redis-backed retry queue with exponential backoff). Created by Codex.",
        "tags": {"agent": "codex", "type": "file"},
    },
    {
        "content": "File created: adapters/slack.ts (Slack destination adapter). Created by Copilot.",
        "tags": {"agent": "copilot", "type": "file"},
    },
    {
        "content": "File created: adapters/email.ts (email destination adapter). Created by Copilot.",
        "tags": {"agent": "copilot", "type": "file"},
    },
    # --- API ---
    {
        "content": (
            "API: POST /webhooks/:source. Receives inbound webhook payloads, "
            "validates the signature, and enqueues them onto the retry queue "
            "for delivery to configured destinations."
        ),
        "tags": {"type": "api"},
    },
    # --- Bugs ---
    {
        "content": (
            "Bug: Stripe webhook signature validation failing intermittently. "
            "Suspected cause: 5-second timestamp tolerance too strict under "
            "network latency. Status: open, unassigned."
        ),
        "tags": {"type": "bug", "status": "open"},
    },
    # --- Dependencies ---
    {
        "content": "RelayCLI depends on: ioredis, zod, commander.",
        "tags": {"type": "dependency"},
    },
]


def main() -> None:
    ok, failed = 0, 0
    for entry in ENTRIES:
        try:
            resp = requests.post(f"{BRIDGE_URL}/remember", json=entry, timeout=120)
            resp.raise_for_status()
            ok += 1
            print(f"remembered: {entry['content'][:60]}...")
        except requests.RequestException as exc:
            failed += 1
            print(f"FAILED: {entry['content'][:60]}... ({exc})", file=sys.stderr)
        time.sleep(0.2)

    print(f"\nSeed complete: {ok} ok, {failed} failed, {len(ENTRIES)} total.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
