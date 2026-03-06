from __future__ import annotations
import shutil
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.domain.pipeline import run_pipeline
from app.domain.settings import AppSettings
from app.models.schemas import JobResult, JobState
from app.services.job_store import job_store


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
    )


def create_job_from_upload(file: UploadFile, remove_audio: bool, model_size: str) -> JobState:
    job_id = str(uuid4())
    workdir = Path(settings.workdir_root) / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or 'input.mp4').suffix or '.mp4'
    video_path = workdir / f'input{suffix}'

    with video_path.open('wb') as f:
        shutil.copyfileobj(file.file, f)

    state = JobState(job_id=job_id, status='queued', stage='queued', progress=0, filename=file.filename)
    job_store.set(state)

    thread = threading.Thread(
        target=_run_job,
        kwargs={
            'job_id': job_id,
            'video_path': str(video_path),
            'workdir': str(workdir),
            'remove_audio': remove_audio,
            'model_size': model_size,
        },
        daemon=True,
    )
    thread.start()
    return state


def _run_job(job_id: str, video_path: str, workdir: str, remove_audio: bool, model_size: str) -> None:
    try:
        job_store.update(job_id, status='processing', stage='probe', progress=10)
        job_store.update(job_id, stage='extract_audio', progress=25)
        job_store.update(job_id, stage='asr', progress=45)
        job_store.update(job_id, stage='render', progress=70)

        result = run_pipeline(
            video_path=video_path,
            workdir=workdir,
            model_size=model_size,
            remove_audio=remove_audio,
            max_chars_per_line=18,
            max_lines=2,
            settings=_app_settings(),
        )

        payload = JobResult(
            resolution=result['resolution'],
            fontsize=result['fontsize'],
            margin_v=result['margin_v'],
            segments=result['segments'],
            download_urls={
                'srt': f'/api/v1/jobs/{job_id}/files/subtitles',
                'video': f'/api/v1/jobs/{job_id}/files/video',
            },
        )
        job_store.update(job_id, status='completed', stage='done', progress=100, result=payload)
    except Exception as exc:
        job_store.update(job_id, status='failed', stage='failed', progress=100, error=str(exc))
