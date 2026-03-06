import json
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


def extract_audio(video_path: str, wav_path: str) -> None:
    _run(['ffmpeg', '-y', '-i', video_path, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', wav_path])


def burn_in_subtitles(video_path: str, srt_path: str, output_path: str, remove_audio: bool, force_style: str) -> None:
    vf = f"subtitles={Path(srt_path).as_posix()}:force_style='{force_style}'"
    cmd = ['ffmpeg', '-y', '-i', video_path, '-vf', vf]
    cmd += ['-an'] if remove_audio else ['-c:a', 'copy']
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', output_path]
    _run(cmd)


def validate_output_video(path: str) -> None:
    _run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', path])
