from typing import List
from app.domain.subtitles import Segment

_model_cache = {}


def transcribe_zh(wav_path: str, model_size: str = 'small') -> List[Segment]:
    from faster_whisper import WhisperModel

    if model_size not in _model_cache:
        _model_cache[model_size] = WhisperModel(model_size, device='cpu', compute_type='int8')
    model = _model_cache[model_size]
    segments, _info = model.transcribe(wav_path, language='zh', vad_filter=True, beam_size=5)
    return [Segment(start=float(s.start), end=float(s.end), text=s.text) for s in segments]
