from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = 'development'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    cors_origins: str = 'http://127.0.0.1:3000,http://localhost:3000'
    max_upload_mb: int = 500
    default_model_size: str = 'small'
    workdir_root: str = './workdir'
    asr_model_root: str = '/app/models'

    fontsize_ratio: float = 0.032
    fontsize_min: int = 14
    fontsize_max: int = 40
    marginv_ratio: float = 0.035
    marginv_min: int = 14
    marginv_max: int = 52
    subtitle_font_name: str = 'Noto Sans CJK SC'

    @field_validator('default_model_size')
    @classmethod
    def validate_model_size(cls, v: str) -> str:
        allowed = {'tiny', 'base', 'small', 'medium', 'large', 'larger', 'large-v3'}
        if v not in allowed:
            raise ValueError(f'default_model_size must be one of {allowed}')
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]

    class Config:
        env_file = '../.env'
        extra = 'ignore'

settings = Settings()
