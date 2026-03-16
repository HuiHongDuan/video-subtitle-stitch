#!/usr/bin/env bash
set -euo pipefail

detect_lan_ip() {
  if command -v ipconfig >/dev/null 2>&1; then
    for iface in en0 en1; do
      local ip
      ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
      if [[ -n "${ip}" ]]; then
        echo "${ip}"
        return 0
      fi
    done
  fi

  if command -v hostname >/dev/null 2>&1; then
    local ip
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
    if [[ -n "${ip}" ]]; then
      echo "${ip}"
      return 0
    fi
  fi

  return 1
}

LAN_IP="${1:-${LAN_IP:-}}"
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="$(detect_lan_ip || true)"
fi

if [[ -z "${LAN_IP}" ]]; then
  echo "[ERROR] 无法自动识别局域网 IP。请执行: ./scripts/docker_up_lan.sh 192.168.x.x"
  exit 1
fi

mkdir -p backend/workdir

export CORS_ORIGINS="http://127.0.0.1:3000,http://localhost:3000,http://${LAN_IP}:3000"
export VITE_API_BASE_URL="http://${LAN_IP}:8000/api"

docker compose up -d --build

echo "[DONE] Docker services started for LAN debugging."
echo "- frontend: http://${LAN_IP}:3000"
echo "- backend:  http://${LAN_IP}:8000/healthz"
echo "- CORS_ORIGINS=${CORS_ORIGINS}"
echo "- VITE_API_BASE_URL=${VITE_API_BASE_URL}"
