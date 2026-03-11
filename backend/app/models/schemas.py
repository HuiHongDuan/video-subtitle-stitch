from typing import Literal, Optional
from pydantic import BaseModel

JobStatus = Literal['queued', 'processing', 'completed', 'failed']
JobStage = Literal['queued', 'probe', 'clip', 'extract_audio', 'asr', 'render', 'export_silent', 'done', 'failed']

class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int


class ErrorResponse(BaseModel):
    error: str
    code: str

class Resolution(BaseModel):
    width: int
    height: int

class JobResult(BaseModel):
    resolution: Resolution
    fontsize: int
    margin_v: int
    segments: int
    model_path: str
    model_size: str
    input_duration: float
    output_duration: float
    silent_duration: float
    clip_range_sec: list[float]
    download_urls: dict[str, str]

class JobState(BaseModel):
    job_id: str
    status: JobStatus
    stage: JobStage
    progress: int
    filename: Optional[str] = None
    error: Optional[str] = None
    result: Optional[JobResult] = None


class ModelOption(BaseModel):
    key: str


class ModelsResponse(BaseModel):
    default: str
    options: list[ModelOption]
