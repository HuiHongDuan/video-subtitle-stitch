#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build

echo "[DONE] Docker services started."
echo "- frontend: http://127.0.0.1:3000"
echo "- backend:  http://127.0.0.1:8000/healthz"
