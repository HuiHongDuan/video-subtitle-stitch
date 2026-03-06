from pydantic import BaseModel

class AppSettings(BaseModel):
    max_upload_mb: int = 500
    max_chars_per_line: int = 18
    max_lines: int = 2
    default_model_size: str = 'small'
    fontsize_ratio: float = 0.05
    fontsize_min: int = 18
    fontsize_max: int = 56
    marginv_ratio: float = 0.06
    marginv_min: int = 24
    marginv_max: int = 80
