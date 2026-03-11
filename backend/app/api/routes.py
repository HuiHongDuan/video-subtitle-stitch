from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import (
    CreateJobResponse,
    ErrorResponse,
    JobState,
    ModelOption,
    ModelsResponse,
    UploadResponse,
)
from app.services.job_store import job_store
from app.services.pipeline_service import (
    create_job_from_upload,
    create_job_from_upload_id,
    list_available_models,
    save_upload,
    validate_model_size,
)

router = APIRouter(prefix='/api/v1', tags=['jobs'])


@router.get('/models', response_model=ModelsResponse)
def list_models():
    detected = list_available_models()
    options = [ModelOption(key=item) for item in detected]
    default_model = settings.default_model_size if settings.default_model_size in detected else detected[0]
    return ModelsResponse(default=default_model, options=options)


@router.post('/uploads', response_model=UploadResponse, responses={400: {'model': ErrorResponse}})
async def upload_file(file: UploadFile = File(...)):
    try:
        asset = save_upload(file)
        return UploadResponse(upload_id=asset.upload_id, filename=asset.filename, size_bytes=asset.size_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={'error': str(exc), 'code': 'BAD_UPLOAD'}) from exc


@router.post('/jobs', response_model=CreateJobResponse, responses={400: {'model': ErrorResponse}})
async def create_job(
    file: UploadFile | None = File(default=None),
    upload_id: str | None = Form(default=None),
    remove_audio: bool = Form(False),
    model_size: str = Form(settings.default_model_size),
    clip_start_sec: float = Form(0.0),
    clip_end_sec: float | None = Form(default=None),
):
    try:
        validate_model_size(model_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={'error': str(exc), 'code': 'INVALID_MODEL_SIZE'}) from exc

    if upload_id:
        try:
            state = create_job_from_upload_id(
                upload_id=upload_id,
                remove_audio=remove_audio,
                model_size=model_size,
                clip_start_sec=clip_start_sec,
                clip_end_sec=clip_end_sec,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={'error': str(exc), 'code': 'BAD_UPLOAD_ID'}) from exc
    elif file:
        try:
            state = create_job_from_upload(
                file=file,
                remove_audio=remove_audio,
                model_size=model_size,
                clip_start_sec=clip_start_sec,
                clip_end_sec=clip_end_sec,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail={'error': str(exc), 'code': 'BAD_UPLOAD'}) from exc
    else:
        raise HTTPException(status_code=400, detail={'error': 'file or upload_id is required', 'code': 'INVALID_REQUEST'})

    return CreateJobResponse(job_id=state.job_id, status=state.status)


@router.get('/jobs/{job_id}', response_model=JobState, responses={404: {'model': ErrorResponse}})
def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={'error': 'Job not found', 'code': 'JOB_NOT_FOUND'})
    return job


@router.get('/jobs/{job_id}/files/subtitles', responses={404: {'model': ErrorResponse}})
def download_subtitles(job_id: str):
    path = Path(settings.workdir_root) / job_id / 'subtitles.srt'
    if not path.exists():
        raise HTTPException(status_code=404, detail={'error': 'Subtitle file not found', 'code': 'FILE_NOT_FOUND'})
    return FileResponse(path, media_type='text/plain', filename='subtitles.srt')


@router.get('/jobs/{job_id}/files/video', responses={404: {'model': ErrorResponse}})
def download_video(job_id: str):
    path = Path(settings.workdir_root) / job_id / 'output.mp4'
    if not path.exists():
        raise HTTPException(status_code=404, detail={'error': 'Video file not found', 'code': 'FILE_NOT_FOUND'})
    return FileResponse(path, media_type='video/mp4', filename='output.mp4')


@router.get('/jobs/{job_id}/files/video_silent', responses={404: {'model': ErrorResponse}})
def download_silent_video(job_id: str):
    path = Path(settings.workdir_root) / job_id / 'silent_clean.mp4'
    if not path.exists():
        raise HTTPException(status_code=404, detail={'error': 'Silent video file not found', 'code': 'FILE_NOT_FOUND'})
    return FileResponse(path, media_type='video/mp4', filename='silent_clean.mp4')
