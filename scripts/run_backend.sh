#!/usr/bin/env bash
set -euo pipefail

cd backend

if [[ ! -d .venv ]]; then
  echo "[ERROR] backend/.venv 不存在，请先执行 ./scripts/install_macos.sh 或手动安装依赖"
  exit 1
fi

source .venv/bin/activate

if ! python -c "import uvicorn" >/dev/null 2>&1; then
  echo "[ERROR] 当前虚拟环境缺少 uvicorn，请执行: python -m pip install -r requirements.txt"
  exit 1
fi

exec python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
