#!/usr/bin/env bash
# One-time setup: install bridge + CLI deps, load seed data.
# Requires .env populated with COGNEE_API_KEY / LLM_API_KEY (see .env.example).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Installing bridge (Python) dependencies"
python -m pip install -r bridge/requirements.txt

echo "==> Installing CLI (Node) dependencies"
(cd cli && npm install && npm run build)

echo "==> Starting bridge in the background"
(cd bridge && uvicorn main:app --host 0.0.0.0 --port 8000 &)
sleep 3

echo "==> Seeding RelayCLI demo data into Cognee"
python -m pip install requests --quiet
python seed/seed_data.py

echo "==> Setup complete. Try: node cli/dist/index.js status"
