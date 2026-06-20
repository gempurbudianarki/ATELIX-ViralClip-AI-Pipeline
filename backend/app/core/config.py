"""
ATELIX ViralClip AI Pipeline — Core Configuration
Loads environment variables and provides typed settings via pydantic-settings.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "change-me-to-random-string"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+asyncpg://ai_cliper:ai_cliper_secret@localhost:5432/ai_cliper"
    database_url_sync: str = "postgresql://ai_cliper:ai_cliper_secret@localhost:5432/ai_cliper"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    openai_api_key: str = ""
    opencode_mcp_enabled: bool = True
    opencode_binary_path: str = "opencode"

    whisper_model_size: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"

    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    tiktok_username: str = ""
    tiktok_password: str = ""
    tiktok_headless: bool = False
    tiktok_proxy: str = ""

    data_dir: str = "./data"
    temp_dir: str = "./data/temp"
    output_dir: str = "./data/output"
    models_dir: str = "./data/models"

    max_video_duration_seconds: int = 7200
    max_clip_duration_seconds: int = 180
    default_clip_duration_seconds: int = 60

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def temp_path(self) -> Path:
        return Path(self.temp_dir).resolve()

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir).resolve()

    @property
    def models_path(self) -> Path:
        return Path(self.models_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
