from pathlib import Path
from typing import Dict

from app.domain.asr import resolve_runtime_model_source, transcribe_zh
from app.domain.settings import AppSettings
from app.domain.subtitles import segments_to_srt
from app.domain.video import burn_in_subtitles, extract_audio, probe_resolution


def _clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def _adaptive_subtitle_style(
    width: int,
    height: int,
    max_chars_per_line: int,
    max_lines: int,
    settings: AppSettings,
) -> tuple[int, int]:
    font = float(height) * settings.fontsize_ratio

    # High-resolution sources need proportionally smaller subtitles.
    if width >= 2560:
        font *= 0.82
    elif width >= 1920:
        font *= 0.86
    elif width >= 1600:
        font *= 0.90
    elif width <= 960:
        font *= 1.05

    # Two-line subtitles should not dominate the frame.
    if max_lines >= 2:
        font *= 0.92

    if max_chars_per_line <= 14:
        font *= 1.06
    elif max_chars_per_line >= 22:
        font *= 0.92

    # User-requested tuning: shrink current subtitle size by another 25%.
    font *= 0.75
    fontsize = _clamp(int(round(font)), settings.fontsize_min, settings.fontsize_max)

    margin = float(height) * settings.marginv_ratio
    if width >= 1920:
        margin *= 0.90

    # User-requested tuning: shorten bottom gap by 50%.
    margin *= 0.50

    # Keep multi-line subtitles readable and avoid clipping near bottom.
    safe_multiline_margin = fontsize * (0.35 + max(0, max_lines - 1) * 0.45)
    margin = max(margin, safe_multiline_margin)

    margin_v = _clamp(int(round(margin)), settings.marginv_min, settings.marginv_max)
    return fontsize, margin_v


def run_pipeline(
    video_path: str,
    workdir: str,
    model_size: str,
    remove_audio: bool,
    max_chars_per_line: int,
    max_lines: int,
    artifact_suffix: str = '',
    settings: AppSettings | None = None,
) -> Dict:
    settings = settings or AppSettings()
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)

    suffix = artifact_suffix.strip()
    audio_path = wd / f'audio{suffix}.wav'
    srt_path = wd / f'subtitles{suffix}.srt'
    out_video = wd / f'output{suffix}.mp4'

    width, height = probe_resolution(video_path)
    fontsize, margin_v = _adaptive_subtitle_style(
        width=width,
        height=height,
        max_chars_per_line=max_chars_per_line,
        max_lines=max_lines,
        settings=settings,
    )

    extract_audio(video_path, str(audio_path))
    segs = transcribe_zh(str(audio_path), model_size=model_size)
    srt_text = segments_to_srt(segs, max_chars_per_line=max_chars_per_line, max_lines=max_lines)
    srt_path.write_text(srt_text, encoding='utf-8')

    font_name = settings.subtitle_font_name.replace(',', ' ').strip() or 'Noto Sans CJK SC'
    force_style = f'Alignment=2,MarginV={margin_v},Outline=1,Shadow=0,Fontsize={fontsize},FontName={font_name}'
    model_path, _is_local = resolve_runtime_model_source(model_size)
    burn_in_subtitles(video_path=video_path, srt_path=str(srt_path), output_path=str(out_video), remove_audio=remove_audio, force_style=force_style)

    return {
        'resolution': {'width': width, 'height': height},
        'fontsize': fontsize,
        'margin_v': margin_v,
        'audio_path': str(audio_path),
        'srt_path': str(srt_path),
        'output_video_path': str(out_video),
        'segments': len(segs),
        'model_path': model_path,
        'model_size': model_size,
    }
