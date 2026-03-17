from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.domain.asr import normalize_model_size, resolve_runtime_model_source
from app.domain.pipeline import run_pipeline
from app.domain.settings import AppSettings
from app.domain.video import export_silent_video, probe_duration, trim_video
from app.models.schemas import JobResult, JobState
from app.services.job_store import job_store
from app.services.upload_store import UploadedAsset, upload_store

ALLOWED_MODEL_SIZES = {'tiny', 'base', 'small', 'medium', 'large', 'larger', 'large-v3'}
PREFERRED_MODEL_SIZES = ('tiny', 'base', 'small', 'medium', 'large')
logger = logging.getLogger(__name__)


def _app_settings() -> AppSettings:
    return AppSettings(
        max_upload_mb=settings.max_upload_mb,
        default_model_size=settings.default_model_size,
        fontsize_ratio=settings.fontsize_ratio,
        fontsize_min=settings.fontsize_min,
        fontsize_max=settings.fontsize_max,
        marginv_ratio=settings.marginv_ratio,
        marginv_min=settings.marginv_min,
        marginv_max=settings.marginv_max,
        subtitle_font_name=settings.subtitle_font_name,
    )


def validate_model_size(model_size: str) -> str:
    if model_size not in ALLOWED_MODEL_SIZES:
        raise ValueError(f'model_size must be one of {sorted(ALLOWED_MODEL_SIZES)}')
    return model_size


def list_available_models() -> list[str]:
    model_root = settings.asr_model_root
    available: list[str] = []

    for option in PREFERRED_MODEL_SIZES:
        canonical = normalize_model_size(option)
        candidates = [
            Path(option),
            Path(canonical),
            Path(model_root) / option,
            Path(model_root) / canonical,
            Path(model_root) / f'faster-whisper-{option}',
            Path(model_root) / f'faster-whisper-{canonical}',
            Path(model_root) / f'whisper-{option}',
            Path(model_root) / f'whisper-{canonical}',
        ]
        if any(p.exists() for p in candidates):
            available.append(option)

    # If the service has no bundled local models, allow standard models so
    # faster-whisper can download them on first use in remote environments.
    return available if available else list(PREFERRED_MODEL_SIZES)


def save_upload(file: UploadFile) -> UploadedAsset:
    upload_id = str(uuid4())
    workdir = Path(settings.workdir_root) / 'uploads'
    workdir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or 'input.mp4').suffix or '.mp4'
    video_path = workdir / f'{upload_id}{suffix}'

    with video_path.open('wb') as f:
        shutil.copyfileobj(file.file, f)

    size_bytes = video_path.stat().st_size
    limit_bytes = settings.max_upload_mb * 1024 * 1024
    if size_bytes > limit_bytes:
        video_path.unlink(missing_ok=True)
        raise ValueError(f'file exceeds max_upload_mb={settings.max_upload_mb}')

    asset = UploadedAsset(
        upload_id=upload_id,
        path=video_path,
        filename=file.filename or video_path.name,
        size_bytes=size_bytes,
    )
    upload_store.set(asset)
    return asset


def create_job_from_upload(
    file: UploadFile, remove_audio: bool, model_size: str, clip_start_sec: float = 0.0, clip_end_sec: float | None = None
) -> JobState:
    asset = save_upload(file)
    return create_job_from_upload_id(
        upload_id=asset.upload_id,
        remove_audio=remove_audio,
        model_size=model_size,
        clip_start_sec=clip_start_sec,
        clip_end_sec=clip_end_sec,
    )


def create_job_from_upload_id(
    upload_id: str, remove_audio: bool, model_size: str, clip_start_sec: float = 0.0, clip_end_sec: float | None = None
) -> JobState:
    validate_model_size(model_size)
    asset = upload_store.get(upload_id)
    if not asset:
        raise ValueError('upload_id not found')

    if clip_start_sec < 0:
        raise ValueError('clip_start_sec must be >= 0')
    if clip_end_sec is not None and clip_end_sec <= clip_start_sec:
        raise ValueError('clip_end_sec must be greater than clip_start_sec')

    job_id = str(uuid4())
    workdir = Path(settings.workdir_root) / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    video_path = workdir / f'input{asset.path.suffix or ".mp4"}'
    shutil.copy(asset.path, video_path)

    state = JobState(job_id=job_id, status='queued', stage='queued', progress=0, filename=asset.filename)
    job_store.set(state)

    thread = threading.Thread(
        target=_run_job,
        kwargs={
            'job_id': job_id,
            'video_path': str(video_path),
            'workdir': str(workdir),
            'remove_audio': remove_audio,
            'model_size': model_size,
            'clip_start_sec': clip_start_sec,
            'clip_end_sec': clip_end_sec,
        },
        daemon=True,
    )
    thread.start()
    return state


def _run_job(
    job_id: str,
    video_path: str,
    workdir: str,
    remove_audio: bool,
    model_size: str,
    clip_start_sec: float = 0.0,
    clip_end_sec: float | None = None,
) -> None:
    try:
        job_store.update(job_id, status='processing', stage='probe', progress=10)
        input_duration = probe_duration(video_path)
        clip_start = max(0.0, float(clip_start_sec))
        clip_end = input_duration if clip_end_sec is None else min(float(clip_end_sec), input_duration)

        if clip_end - clip_start < 0.2:
            raise RuntimeError('clip range is too short, please keep at least 0.2s')

        pipeline_video_path = video_path
        if clip_start > 0.0 or clip_end < input_duration:
            job_store.update(job_id, stage='clip', progress=22)
            clipped_path = Path(workdir) / 'input_clip.mp4'
            trim_video(video_path=video_path, output_path=str(clipped_path), start_sec=clip_start, end_sec=clip_end)
            pipeline_video_path = str(clipped_path)

        job_store.update(job_id, stage='extract_audio', progress=35)
        job_store.update(job_id, stage='asr', progress=50)
        job_store.update(job_id, stage='render', progress=75)

        result = run_pipeline(
            video_path=pipeline_video_path,
            workdir=workdir,
            model_size=model_size,
            remove_audio=remove_audio,
            max_chars_per_line=18,
            max_lines=2,
            settings=_app_settings(),
        )
        job_store.update(job_id, stage='export_silent', progress=90)
        silent_clean_path = Path(workdir) / 'silent_clean.mp4'
        export_silent_video(pipeline_video_path, str(silent_clean_path))

        source_duration = probe_duration(pipeline_video_path)
        output_duration = probe_duration(result['output_video_path'])
        silent_duration = probe_duration(str(silent_clean_path))
        tolerance_sec = 1.0
        if abs(output_duration - source_duration) > tolerance_sec:
            raise RuntimeError(f'output video duration mismatch: input={source_duration:.2f}s output={output_duration:.2f}s')
        if abs(silent_duration - source_duration) > tolerance_sec:
            raise RuntimeError(f'silent video duration mismatch: input={source_duration:.2f}s output={silent_duration:.2f}s')

        payload = JobResult(
            resolution=result['resolution'],
            fontsize=result['fontsize'],
            margin_v=result['margin_v'],
            segments=result['segments'],
            model_path=result.get('model_path') or resolve_runtime_model_source(model_size)[0],
            model_size=result.get('model_size') or model_size,
            input_duration=source_duration,
            output_duration=output_duration,
            silent_duration=silent_duration,
            clip_range_sec=[clip_start, clip_end],
            download_urls={
                'srt': f'/api/v1/jobs/{job_id}/files/subtitles',
                'video': f'/api/v1/jobs/{job_id}/files/video',
                'silent': f'/api/v1/jobs/{job_id}/files/video_silent',
            },
        )
        job_store.update(job_id, status='completed', stage='done', progress=100, result=payload)
    except Exception as exc:
        logger.exception('Job failed: job_id=%s, video_path=%s, workdir=%s', job_id, video_path, workdir)
        job_store.update(job_id, status='failed', stage='failed', progress=100, error=str(exc))
