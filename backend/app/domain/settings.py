from pydantic import BaseModel

class AppSettings(BaseModel):
    max_upload_mb: int = 500
    max_chars_per_line: int = 18
    max_lines: int = 2
    default_model_size: str = 'small'
    fontsize_ratio: float = 0.032
    fontsize_min: int = 14
    fontsize_max: int = 40
    marginv_ratio: float = 0.035
    marginv_min: int = 14
    marginv_max: int = 52
    subtitle_font_name: str = 'Noto Sans CJK SC'
