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

    fontsize_ratio: float = 0.05
    fontsize_min: int = 18
    fontsize_max: int = 56
    marginv_ratio: float = 0.06
    marginv_min: int = 24
    marginv_max: int = 80

    @field_validator('default_model_size')
    @classmethod
    def validate_model_size(cls, v: str) -> str:
        allowed = {'tiny', 'base', 'small', 'medium'}
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
