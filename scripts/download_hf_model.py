#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    repo_id = os.environ.get('HF_MODEL_REPO', 'Systran/faster-whisper-small')
    local_dir = Path(os.environ.get('MODEL_OUTPUT_DIR', 'build-artifacts/models/faster-whisper-small'))
    token = (os.environ.get('HUGGINGFACE_HUB_TOKEN') or '').strip() or None

    local_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        token=token,
        allow_patterns=[
            'config.json',
            'model.bin',
            'tokenizer.json',
            'vocabulary.*',
            'preprocessor_config.json',
            'README.md',
            '.gitattributes',
        ],
    )


if __name__ == '__main__':
    main()
