#!/usr/bin/env bash
set -euo pipefail

command -v brew >/dev/null 2>&1 || { echo "[ERROR] Homebrew 未安装，请先安装：https://brew.sh"; exit 1; }

echo "[INFO] 安装基础依赖 (ffmpeg / python / node)..."
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list python >/dev/null 2>&1 || brew install python
brew list node >/dev/null 2>&1 || brew install node

echo "[INFO] 创建并安装 backend 虚拟环境依赖..."
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -U pip
python -m pip install -r backend/requirements.txt

echo "[INFO] 安装 frontend 依赖..."
cd frontend
npm install

echo "[DONE] 安装完成。"
echo "[NEXT] 启动后端: ./scripts/run_backend.sh"
echo "[NEXT] 启动前端: ./scripts/run_frontend.sh"
