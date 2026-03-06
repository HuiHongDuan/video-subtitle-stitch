import os
from pathlib import Path
import pytest

from app.domain.eval import evaluate_srt
from app.domain.pipeline import run_pipeline
from app.domain.video import validate_output_video

ASSET_VIDEO = Path('tests/assets/sample_3min.mp4')
GOLD_SRT = Path('tests/assets/golden.srt')


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


@pytest.mark.skipif(not ASSET_VIDEO.exists(), reason='Missing tests/assets/sample_3min.mp4')
def test_smoke_pipeline(tmp_path: Path):
    out = run_pipeline(
        video_path=str(ASSET_VIDEO),
        workdir=str(tmp_path),
        model_size=os.getenv('ASR_MODEL_SIZE', 'small'),
        remove_audio=False,
        max_chars_per_line=18,
        max_lines=2,
    )
    srt = Path(out['srt_path'])
    mp4 = Path(out['output_video_path'])
    assert srt.exists() and srt.stat().st_size > 0
    assert mp4.exists() and mp4.stat().st_size > 0
    validate_output_video(str(mp4))
    text = srt.read_text(encoding='utf-8', errors='ignore')
    assert text.count('

') >= 5
    if GOLD_SRT.exists():
        gold_text = GOLD_SRT.read_text(encoding='utf-8', errors='ignore')
        metrics = evaluate_srt(text, gold_text, min_iou=_env_float('EVAL_MIN_IOU', 0.5))
        assert metrics['coverage'] >= _env_float('EVAL_COVERAGE_TH', 0.70)
        assert metrics['avg_similarity'] >= _env_float('EVAL_SIM_TH', 0.60)
        assert metrics['score'] >= _env_float('EVAL_SCORE_TH', 0.45)
