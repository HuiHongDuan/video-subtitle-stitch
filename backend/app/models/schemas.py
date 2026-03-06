from typing import Literal, Optional
from pydantic import BaseModel

JobStatus = Literal['queued', 'processing', 'completed', 'failed']
JobStage = Literal['queued', 'probe', 'extract_audio', 'asr', 'render', 'done', 'failed']

class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus

class Resolution(BaseModel):
    width: int
    height: int

class JobResult(BaseModel):
    resolution: Resolution
    fontsize: int
    margin_v: int
    segments: int
    download_urls: dict[str, str]

class JobState(BaseModel):
    job_id: str
    status: JobStatus
    stage: JobStage
    progress: int
    filename: Optional[str] = None
    error: Optional[str] = None
    result: Optional[JobResult] = None
