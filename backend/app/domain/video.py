import json
import os
import subprocess
from pathlib import Path
from typing import Tuple


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr}")
    return p


def probe_resolution(video_path: str) -> Tuple[int, int]:
    p = _run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', video_path])
    data = json.loads(p.stdout)
    streams = data.get('streams') or []
    if not streams:
        raise RuntimeError('ffprobe: no video stream found')
    return int(streams[0]['width']), int(streams[0]['height'])


def probe_duration(video_path: str) -> float:
    p = _run(
        [
            'ffprobe',
            '-v',
            'error',
            '-show_entries',
            'format=duration',
            '-of',
            'default=noprint_wrappers=1:nokey=1',
            video_path,
        ]
    )
    value = (p.stdout or '').strip()
    if not value:
        raise RuntimeError('ffprobe: no duration found')
    return float(value)


def extract_audio(video_path: str, wav_path: str) -> None:
    _run(['ffmpeg', '-y', '-i', video_path, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', wav_path])


def _escape_filter_path(path: str) -> str:
    value = Path(path).resolve().as_posix()
    value = value.replace('\\', '\\\\')
    value = value.replace(':', '\\:')
    value = value.replace("'", "\\'")
    value = value.replace(',', '\\,')
    value = value.replace('[', '\\[').replace(']', '\\]')
    return value


def _escape_force_style(style: str) -> str:
    return style.replace('\\', '\\\\').replace("'", "\\'")


def burn_in_subtitles(video_path: str, srt_path: str, output_path: str, remove_audio: bool, force_style: str) -> None:
    escaped_srt = _escape_filter_path(srt_path)
    escaped_style = _escape_force_style(force_style)
    vf = f"subtitles='{escaped_srt}':force_style='{escaped_style}'"
    cmd = ['ffmpeg', '-y', '-i', video_path, '-vf', vf]
    cmd += ['-an'] if remove_audio else ['-c:a', 'copy']
    cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-movflags', '+faststart', output_path]
    _run(cmd)


def export_silent_video(video_path: str, output_path: str) -> None:
    _run(
        [
            'ffmpeg',
            '-y',
            '-i',
            video_path,
            '-an',
            '-c:v',
            'libx264',
            '-preset',
            'ultrafast',
            '-crf',
            '23',
            '-movflags',
            '+faststart',
            output_path,
        ]
    )


def trim_video(video_path: str, output_path: str, start_sec: float, end_sec: float) -> None:
    if start_sec < 0:
        raise ValueError('start_sec must be >= 0')
    if end_sec <= start_sec:
        raise ValueError('end_sec must be greater than start_sec')

    _run(
        [
            'ffmpeg',
            '-y',
            '-ss',
            f'{start_sec:.3f}',
            '-to',
            f'{end_sec:.3f}',
            '-i',
            video_path,
            '-c:v',
            'libx264',
            '-preset',
            'ultrafast',
            '-crf',
            '23',
            '-c:a',
            'aac',
            '-b:a',
            '128k',
            '-movflags',
            '+faststart',
            output_path,
        ]
    )


def export_video_frame(video_path: str, output_path: str, timestamp_sec: float) -> None:
    if timestamp_sec < 0:
        raise ValueError('timestamp_sec must be >= 0')

    def _build_cmd(ts: float) -> list[str]:
        return [
            'ffmpeg',
            '-y',
            '-ss',
            f'{max(0.0, ts):.3f}',
            '-i',
            video_path,
            '-frames:v',
            '1',
            '-an',
            '-vcodec',
            'png',
            '-pix_fmt',
            'rgb24',
            output_path,
        ]

    candidates = [timestamp_sec, timestamp_sec - 0.2, timestamp_sec - 0.8, 0.0]
    last_error: Exception | None = None
    for ts in candidates:
        try:
            _run(_build_cmd(ts))
            return
        except Exception as exc:
            last_error = exc
    if last_error is not None:
        raise last_error


def validate_output_video(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f'Output file not found: {path}')
    _run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', path])
