#!/usr/bin/env bash
# Runs the exact command sequence from docs/demo-script.md, leading with `agent handoff`.
set -euo pipefail
cd "$(dirname "$0")/.."

AGENT="node cli/dist/index.js"

echo "=== agent handoff codex ==="
$AGENT handoff codex

echo -e "\n=== agent status ==="
$AGENT status

echo -e "\n=== agent workspace claude ==="
$AGENT workspace claude

echo -e "\n=== agent assigned codex ==="
$AGENT assigned codex

echo -e "\n=== agent timeline ==="
$AGENT timeline

echo -e "\n=== agent why redis ==="
$AGENT why redis

echo -e "\n=== agent forget (lifecycle demo) ==="
$AGENT forget "HMAC webhook signature validation"
$AGENT status
