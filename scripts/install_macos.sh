#!/usr/bin/env bash
set -euo pipefail

command -v brew >/dev/null 2>&1 || { echo "Homebrew 未安装"; exit 1; }

brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -U pip
pip install -r backend/requirements.txt

cd frontend
npm install
