"""
ATELIX ViralClip AI Pipeline — Video API Routes
Endpoints untuk manajemen video: create, list, detail, delete.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Video, Clip, PipelineStatus
from app.schemas import (
    VideoCreateRequest,
    VideoResponse,
    VideoDetailResponse,
    PipelineStatusResponse,
)
from app.workers.tasks import run_full_pipeline

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/", response_model=VideoResponse, status_code=201)
async def create_video(
    payload: VideoCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    metadata = {}
    if payload.language:
        metadata["language"] = payload.language

    video = Video(
        youtube_url=payload.youtube_url,
        status=PipelineStatus.PENDING,
        metadata_json=metadata,
    )
    db.add(video)
    await db.flush()

    run_full_pipeline.delay(video.id, payload.youtube_url)

    return video


@router.get("/", response_model=list[VideoResponse])
async def list_videos(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Video).order_by(Video.created_at.desc())

    if status:
        query = query.where(Video.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video


@router.get("/{video_id}/status", response_model=PipelineStatusResponse)
async def get_video_status(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    clips_count_result = await db.execute(
        select(func.count(Clip.id)).where(Clip.video_id == video_id)
    )
    clips_count = clips_count_result.scalar() or 0

    return PipelineStatusResponse(
        video_id=video.id,
        status=video.status.value,
        error_message=video.error_message,
        clips_count=clips_count,
    )


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    await db.delete(video)
