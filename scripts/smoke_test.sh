#!/usr/bin/env bash
set -euo pipefail
cd backend
pytest -q tests/test_subtitles.py tests/test_eval.py tests/test_api_contract.py
pytest -q tests/test_pipeline_smoke.py || true
