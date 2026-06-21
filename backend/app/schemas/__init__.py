"""
ATELIX ViralClip AI Pipeline — Pydantic Schemas
Request/Response models for the API layer.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class VideoCreateRequest(BaseModel):
    youtube_url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL video YouTube yang akan diproses",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    language: Optional[str] = Field(
        None,
        description="Kode bahasa (contoh: 'id', 'en', 'auto') atau null untuk auto-detect",
        examples=["id", "en", "auto"],
    )


class VideoResponse(BaseModel):
    id: str
    youtube_url: str
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClipResponse(BaseModel):
    id: str
    clip_index: int
    start_time: float
    end_time: float
    duration: float
    virality_score: Optional[float] = None
    hook_text: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[list[str]] = None
    mood: Optional[str] = None
    output_path: Optional[str] = None
    tiktok_url: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class VideoDetailResponse(VideoResponse):
    clips: list[ClipResponse] = []


class PipelineStatusResponse(BaseModel):
    video_id: str
    status: str
    progress: int = 0
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    clips_count: int = 0


class TranscriptionResponse(BaseModel):
    language: Optional[str] = None
    full_text: Optional[str] = None
    segments_count: int = 0
    words_count: int = 0


class PublishRequest(BaseModel):
    clip_id: str


class PublishResponse(BaseModel):
    clip_id: str
    tiktok_url: Optional[str] = None
    status: str
