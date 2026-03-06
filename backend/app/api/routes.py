from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import CreateJobResponse, JobState
from app.services.job_store import job_store
from app.services.pipeline_service import create_job_from_upload

router = APIRouter(prefix='/api/v1', tags=['jobs'])

@router.post('/jobs', response_model=CreateJobResponse)
async def create_job(
    file: UploadFile = File(...),
    remove_audio: bool = Form(False),
    model_size: str = Form(settings.default_model_size),
):
    state = create_job_from_upload(file=file, remove_audio=remove_audio, model_size=model_size)
    return CreateJobResponse(job_id=state.job_id, status=state.status)

@router.get('/jobs/{job_id}', response_model=JobState)
def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job

@router.get('/jobs/{job_id}/files/subtitles')
def download_subtitles(job_id: str):
    path = Path(settings.workdir_root) / job_id / 'subtitles.srt'
    if not path.exists():
        raise HTTPException(status_code=404, detail='Subtitle file not found')
    return FileResponse(path, media_type='text/plain', filename='subtitles.srt')

@router.get('/jobs/{job_id}/files/video')
def download_video(job_id: str):
    path = Path(settings.workdir_root) / job_id / 'output.mp4'
    if not path.exists():
        raise HTTPException(status_code=404, detail='Video file not found')
    return FileResponse(path, media_type='video/mp4', filename='output.mp4')
