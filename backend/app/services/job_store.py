from __future__ import annotations
from threading import Lock
from typing import Dict, Optional
from app.models.schemas import JobState

class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobState] = {}
        self._lock = Lock()

    def set(self, job: JobState) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Optional[JobState]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> Optional[JobState]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            updated = job.model_copy(update=fields)
            self._jobs[job_id] = updated
            return updated

job_store = JobStore()
