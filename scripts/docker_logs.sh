#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-backend}"

case "$SERVICE" in
  all)
    docker compose logs -f --tail=200
    ;;
  backend|frontend)
    docker compose logs -f --tail=200 "$SERVICE"
    ;;
  *)
    echo "[ERROR] Usage: ./scripts/docker_logs.sh [backend|frontend|all]"
    exit 1
    ;;
esac
