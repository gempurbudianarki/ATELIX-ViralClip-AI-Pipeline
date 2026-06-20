"""
ATELIX ViralClip AI Pipeline — Pipeline API Routes
Endpoints untuk monitoring pipeline, clips, dan publishing.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Video, Clip, PipelineTask
from app.schemas import ClipResponse, PublishRequest, PublishResponse
from app.workers.tasks import publish_clip_to_tiktok

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/tasks/{video_id}", response_model=list[dict])
async def get_pipeline_tasks(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PipelineTask)
        .where(PipelineTask.video_id == video_id)
        .order_by(PipelineTask.created_at.asc())
    )
    tasks = result.scalars().all()

    return [
        {
            "id": t.id,
            "task_type": t.task_type,
            "status": t.status.value,
            "progress": t.progress,
            "error_message": t.error_message,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


@router.get("/clips/{video_id}", response_model=list[ClipResponse])
async def get_clips(
    video_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Clip)
        .where(Clip.video_id == video_id)
        .order_by(Clip.clip_index.asc())
    )
    return result.scalars().all()


@router.post("/publish", response_model=PublishResponse)
async def publish_clip(
    payload: PublishRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Clip).where(Clip.id == payload.clip_id))
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if not clip.output_path:
        raise HTTPException(status_code=400, detail="Clip has not been rendered yet")

    publish_clip_to_tiktok.delay(clip.id, clip.output_path, clip.caption, clip.hashtags)

    return PublishResponse(
        clip_id=clip.id,
        status="publishing",
    )
