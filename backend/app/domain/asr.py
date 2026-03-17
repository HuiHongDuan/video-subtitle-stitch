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


def resolve_runtime_model_source(model_size: str) -> tuple[str, bool]:
    local_model = resolve_local_model_path(model_size)
    if local_model:
        return local_model, True
    return normalize_model_size(model_size), False


def transcribe_zh(wav_path: str, model_size: str = 'small') -> list[Segment]:
    from faster_whisper import WhisperModel

    model_source, is_local = resolve_runtime_model_source(model_size)
    key_prefix = 'local' if is_local else 'remote'
    key = f'{key_prefix}::{model_source}'
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(model_source, device='cpu', compute_type='int8')
    model = _model_cache[key]

    segments, _info = model.transcribe(wav_path, language='zh', vad_filter=True, beam_size=5)
    return [Segment(start=float(s.start), end=float(s.end), text=s.text) for s in segments]
