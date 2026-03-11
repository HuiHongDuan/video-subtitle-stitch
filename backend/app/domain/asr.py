import os
from pathlib import Path
from typing import Optional

from app.domain.subtitles import Segment

_model_cache: dict[str, object] = {}

_MODEL_ALIASES = {
    'larger': 'large-v3',
    'large': 'large-v3',
}


def normalize_model_size(model_size: str) -> str:
    return _MODEL_ALIASES.get(model_size, model_size)


def resolve_local_model_path(model_size: str, model_root: str = 'models') -> Optional[str]:
    requested = model_size
    canonical = normalize_model_size(model_size)

    direct_candidates = [Path(requested)]
    if canonical != requested:
        direct_candidates.append(Path(canonical))

    for candidate in direct_candidates:
        if candidate.exists():
            return str(candidate)

    root = Path(os.getenv('ASR_MODEL_ROOT', model_root))
    size_candidates = [requested]
    if canonical != requested:
        size_candidates.append(canonical)

    candidates: list[Path] = []
    for size in size_candidates:
        candidates.extend(
            [
                root / size,
                root / f'faster-whisper-{size}',
                root / f'whisper-{size}',
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def transcribe_zh(wav_path: str, model_size: str = 'small') -> list[Segment]:
    from faster_whisper import WhisperModel

    local_model = resolve_local_model_path(model_size)
    if not local_model:
        requested = model_size
        canonical = normalize_model_size(model_size)
        example = f'backend/models/{canonical}'
        raise RuntimeError(
            f"Local Whisper model not found for '{requested}'. "
            'Please place model files under ASR_MODEL_ROOT (default: /app/models in Docker, ./backend/models on host), '
            f'for example: {example}.'
        )

    key = f'local::{local_model}'
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(local_model, device='cpu', compute_type='int8')
    model = _model_cache[key]

    segments, _info = model.transcribe(wav_path, language='zh', vad_filter=True, beam_size=5)
    return [Segment(start=float(s.start), end=float(s.end), text=s.text) for s in segments]
