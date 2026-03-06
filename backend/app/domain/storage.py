import uuid
from pathlib import Path


def new_session_dir(root: str = 'workdir') -> Path:
    sid = str(uuid.uuid4())
    p = Path(root) / sid
    p.mkdir(parents=True, exist_ok=True)
    return p
