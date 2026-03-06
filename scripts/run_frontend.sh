#!/usr/bin/env bash
set -euo pipefail

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm 未安装。macOS 可执行: brew install node"
  exit 1
fi

cd frontend

if [[ ! -d node_modules ]]; then
  echo "[INFO] 检测到 frontend/node_modules 缺失，先执行 npm install..."
  npm install
fi

exec npm run dev
