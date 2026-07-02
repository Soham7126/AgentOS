# AgentOS — Claude Code Session Context

## What this project is
AgentOS is a CLI coordination layer for multi-agent coding teams,
backed by Cognee Cloud as the shared knowledge graph. Read PRD.md
for the full picture.

## Four files to read before writing any code
1. PRD.md — problem, goals, tech stack, judging criteria
2. ARCHITECTURE.md — system design, component breakdown, data model
3. FEATURES.md — all 6 features with commands, example I/O, acceptance criteria
4. TASKS.md — 3-day build plan, ordered by dependency

## Folder structure to build (from ARCHITECTURE.md §5)
cli/          → Node.js + TypeScript + Commander.js (the CLI)
bridge/       → Python + FastAPI (wraps Cognee SDK, 4 endpoints only)
seed/         → Python seed script for RelayCLI demo data
integrations/ → claude-code and codex only (already copied in)
demo-app/     → RelayCLI (the fictional app agents are building)
docs/         → architecture.md, demo-script.md, judging-checklist.md
scripts/      → setup.sh, demo.sh

## Current state
Nothing built yet. Start with bridge/ — it unblocks everything else.

## Cognee reference
- Repo is at ../cognee (sibling folder)
- Integrations are at ../cognee-integrations (sibling folder)
- Installed integrations copied into ./integrations/claude-code and ./integrations/codex
- SDK is Python only — all Cognee calls go through bridge/, never from cli/ directly

## Key decisions already made
- Cognee Cloud track (not self-hosted)
- Node/TypeScript for CLI, Python/FastAPI for bridge
- Only claude-code and codex integrations used
- RelayCLI (webhook relay tool) is the demo subject app
- agent handoff is the centerpiece feature — build and test this first on Day 2

## What NOT to do
- Do not call Cognee SDK directly from cli/ — only through bridge/
- Do not add features beyond the 6 in FEATURES.md
- Do not install integrations other than claude-code and codex