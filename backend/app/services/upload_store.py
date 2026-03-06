from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, Optional


@dataclass
class UploadedAsset:
    upload_id: str
    path: Path
    filename: str
    size_bytes: int


class UploadStore:
    def __init__(self) -> None:
        self._uploads: Dict[str, UploadedAsset] = {}
        self._lock = Lock()

    def set(self, item: UploadedAsset) -> None:
        with self._lock:
            self._uploads[item.upload_id] = item

    def get(self, upload_id: str) -> Optional[UploadedAsset]:
        with self._lock:
            return self._uploads.get(upload_id)


upload_store = UploadStore()
