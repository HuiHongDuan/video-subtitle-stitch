from pathlib import Path
from typing import Dict
from app.domain.asr import transcribe_zh
from app.domain.settings import AppSettings
from app.domain.subtitles import segments_to_srt
from app.domain.video import burn_in_subtitles, extract_audio, probe_resolution


def _clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def run_pipeline(video_path: str, workdir: str, model_size: str, remove_audio: bool, max_chars_per_line: int, max_lines: int, settings: AppSettings | None = None) -> Dict:
    settings = settings or AppSettings()
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)

    audio_path = wd / 'audio.wav'
    srt_path = wd / 'subtitles.srt'
    out_video = wd / 'output.mp4'

    width, height = probe_resolution(video_path)
    fontsize = _clamp(int(round(height * settings.fontsize_ratio)), settings.fontsize_min, settings.fontsize_max)
    margin_v = _clamp(int(round(height * settings.marginv_ratio)), settings.marginv_min, settings.marginv_max)

    extract_audio(video_path, str(audio_path))
    segs = transcribe_zh(str(audio_path), model_size=model_size)
    srt_text = segments_to_srt(segs, max_chars_per_line=max_chars_per_line, max_lines=max_lines)
    srt_path.write_text(srt_text, encoding='utf-8')

    force_style = f'Alignment=2,MarginV={margin_v},Outline=2,Shadow=1,Fontsize={fontsize}'
    burn_in_subtitles(video_path=video_path, srt_path=str(srt_path), output_path=str(out_video), remove_audio=remove_audio, force_style=force_style)

    return {
        'resolution': {'width': width, 'height': height},
        'fontsize': fontsize,
        'margin_v': margin_v,
        'audio_path': str(audio_path),
        'srt_path': str(srt_path),
        'output_video_path': str(out_video),
        'segments': len(segs),
    }
