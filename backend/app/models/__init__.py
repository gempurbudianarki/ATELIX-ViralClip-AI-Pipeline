"""
ATELIX ViralClip AI Pipeline — Database Models
Core ORM models for videos, clips, and pipeline tasks.
Works with both PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class PipelineStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    EDITING = "editing"
    RENDERING = "rendering"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Video(Base):
    __tablename__ = "videos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    youtube_url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    resolution = Column(String(32), nullable=True)
    file_path = Column(String(1024), nullable=True)
    thumbnail_url = Column(String(2048), nullable=True)
    status = Column(String(32), default=PipelineStatus.PENDING.value, index=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clips = relationship("Clip", back_populates="video", cascade="all, delete-orphan")
    transcription = relationship(
        "Transcription", back_populates="video", uselist=False, cascade="all, delete-orphan"
    )


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), unique=True, index=True)
    language = Column(String(10), nullable=True)
    full_text = Column(Text, nullable=True)
    segments_json = Column(JSON, nullable=True)
    words_json = Column(JSON, nullable=True)
    silence_segments_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="transcription")


class Clip(Base):
    __tablename__ = "clips"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    clip_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    virality_score = Column(Float, nullable=True)
    hook_text = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    mood = Column(String(32), nullable=True)
    output_path = Column(String(1024), nullable=True)
    tiktok_url = Column(String(2048), nullable=True)
    status = Column(String(32), default=PipelineStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="clips")


class PipelineTask(Base):
    __tablename__ = "pipeline_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    task_type = Column(String(64), nullable=False, index=True)
    celery_task_id = Column(String(128), nullable=True)
    status = Column(String(32), default=PipelineStatus.PENDING.value)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result_json = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
