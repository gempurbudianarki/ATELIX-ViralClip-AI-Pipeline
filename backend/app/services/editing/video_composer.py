"""
ATELIX ViralClip AI Pipeline — Video Composer
Orchestrates the full video editing pipeline: crop, track, subtitle, effects, render.
"""

import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.models import Video, Clip, Transcription, PipelineStatus

settings = get_settings()


def edit_viral_clips(video_id: str) -> dict:
    """
    Phase 1: Prepare all clips for rendering.
    - Extract raw clip segments from source video
    - Analyze face positions for smart cropping
    - Generate subtitle data per clip
    """
    from app.core.database import async_session_factory
    from sqlalchemy import select

    async def _update_status():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = PipelineStatus.EDITING
                await session.commit()

    asyncio.get_event_loop().run_until_complete(_update_status())

    try:
        async def _load_data():
            async with async_session_factory() as session:
                video_result = await session.execute(
                    select(Video).where(Video.id == video_id)
                )
                video = video_result.scalar_one_or_none()

                clips_result = await session.execute(
                    select(Clip)
                    .where(Clip.video_id == video_id)
                    .order_by(Clip.clip_index.asc())
                )
                clips = clips_result.scalars().all()

                trans_result = await session.execute(
                    select(Transcription).where(Transcription.video_id == video_id)
                )
                transcription = trans_result.scalar_one_or_none()

                return video, list(clips), transcription

        video, clips, transcription = asyncio.get_event_loop().run_until_complete(_load_data())

        if not video or not video.file_path:
            raise ValueError("Source video not found")
        if not clips:
            raise ValueError("No clips found to edit")
        if not transcription:
            raise ValueError("Transcription not found")

        source_path = Path(video.file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source video missing: {video.file_path}")

        output_dir = settings.output_path / video_id / "clips"
        output_dir.mkdir(parents=True, exist_ok=True)

        from app.services.editing.face_tracker import analyze_clip_face_positions
        from app.services.editing.subtitle_renderer import prepare_subtitle_data

        prepared_clips = []
        for clip in clips:
            clip_data = {
                "id": clip.id,
                "index": clip.clip_index,
                "start": clip.start_time,
                "end": clip.end_time,
                "duration": clip.duration,
                "virality_score": clip.virality_score,
                "hook_text": clip.hook_text,
                "mood": clip.mood,
                "output_path": str(output_dir / f"clip_{clip.clip_index:03d}.mp4"),
            }

            try:
                face_data = analyze_clip_face_positions(
                    str(source_path),
                    clip.start_time,
                    clip.end_time,
                )
                clip_data["face_tracking"] = face_data
            except Exception as face_error:
                print(f"Warning: face tracking failed for clip {clip.id}: {face_error}")
                clip_data["face_tracking"] = {"method": "error_fallback", "face_detected": False}

            try:
                subtitle_data = prepare_subtitle_data(
                    transcription.words_json or [],
                    clip.start_time,
                    clip.end_time,
                    clip.mood or "neutral",
                )
                clip_data["subtitles"] = subtitle_data
                clip_data["subtitle_count"] = len(subtitle_data)
            except Exception as sub_error:
                print(f"Warning: subtitle generation failed for clip {clip.id}: {sub_error}")
                clip_data["subtitles"] = []
                clip_data["subtitle_count"] = 0

            prepared_clips.append(clip_data)

        async def _save_prepared_data():
            async with async_session_factory() as session:
                for clip_data in prepared_clips:
                    result = await session.execute(
                        select(Clip).where(Clip.id == clip_data["id"])
                    )
                    clip_db = result.scalar_one_or_none()
                    if clip_db:
                        clip_db.metadata_json = {
                            **(clip_db.metadata_json or {}),
                            "face_tracking": clip_data.get("face_tracking"),
                            "subtitle_count": clip_data.get("subtitle_count", 0),
                            "subtitles": clip_data.get("subtitles", []),
                        }
                        clip_db.output_path = clip_data["output_path"]
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_prepared_data())

        return {
            "video_id": video_id,
            "clips_prepared": len(prepared_clips),
            "output_dir": str(output_dir),
            "clips": [
                {
                    "id": c["id"],
                    "index": c["index"],
                    "face_tracking": c.get("face_tracking"),
                    "subtitle_count": c.get("subtitle_count", 0),
                }
                for c in prepared_clips
            ],
            "status": "edited",
        }

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                v = result.scalar_one_or_none()
                if v:
                    v.status = PipelineStatus.FAILED
                    v.error_message = f"Editing failed: {str(e)}"
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise


def render_viral_clips(video_id: str) -> dict:
    """
    Phase 2: Render all prepared clips using FFmpeg with:
    - Smart crop to 9:16 (1080x1920)
    - Face tracking center positioning
    - Dynamic subtitle burn-in
    - Zoom/retention effects
    - Audio enhancement
    """
    from app.core.database import async_session_factory
    from sqlalchemy import select

    async def _update_status():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = PipelineStatus.RENDERING
                await session.commit()

    asyncio.get_event_loop().run_until_complete(_update_status())

    try:
        async def _load_clips():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Clip)
                    .where(Clip.video_id == video_id)
                    .order_by(Clip.clip_index.asc())
                )
                return list(result.scalars().all())

        clips = asyncio.get_event_loop().run_until_complete(_load_clips())

        async def _get_video():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                v = result.scalar_one_or_none()
                return v.file_path if v else None

        source_path = asyncio.get_event_loop().run_until_complete(_get_video())
        if not source_path:
            raise ValueError("Source video path not found")

        from app.services.editing.video_renderer import render_single_clip

        rendered = []
        for clip in clips:
            if not clip.output_path:
                continue

            try:
                face_data = (clip.metadata_json or {}).get("face_tracking")
                subtitle_data = (clip.metadata_json or {}).get("subtitles")

                result = render_single_clip(
                    video_id=video_id,
                    clip_id=clip.id,
                    start_time=clip.start_time,
                    end_time=clip.end_time,
                    output_path=clip.output_path,
                    source_path=str(source_path),
                    face_data=face_data,
                    subtitle_data=subtitle_data,
                    mood=clip.mood or "neutral",
                )
                rendered.append({"clip_id": clip.id, "status": "rendered", **result})
            except Exception as clip_error:
                rendered.append({
                    "clip_id": clip.id,
                    "status": "failed",
                    "error": str(clip_error),
                })
                print(f"Render ERROR for clip {clip.id}: {clip_error}")

        async def _save_render_results():
            async with async_session_factory() as session:
                for r in rendered:
                    if r["status"] == "rendered":
                        result = await session.execute(
                            select(Clip).where(Clip.id == r["clip_id"])
                        )
                        clip_db = result.scalar_one_or_none()
                        if clip_db:
                            clip_db.status = PipelineStatus.COMPLETED

                video_result = await session.execute(
                    select(Video).where(Video.id == video_id)
                )
                vid = video_result.scalar_one_or_none()
                if vid:
                    all_complete = all(r["status"] == "rendered" for r in rendered)
                    vid.status = PipelineStatus.COMPLETED if all_complete else PipelineStatus.FAILED
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_render_results())

        return {
            "video_id": video_id,
            "total_clips": len(clips),
            "rendered": sum(1 for r in rendered if r["status"] == "rendered"),
            "failed": sum(1 for r in rendered if r["status"] == "failed"),
            "details": rendered,
            "status": "rendering_complete",
        }

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                v = result.scalar_one_or_none()
                if v:
                    v.status = PipelineStatus.FAILED
                    v.error_message = f"Rendering failed: {str(e)}"
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise
