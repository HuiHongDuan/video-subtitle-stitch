#!/usr/bin/env bash
set -euo pipefail
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
