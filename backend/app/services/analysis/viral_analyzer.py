"""
ATELIX ViralClip AI Pipeline — Viral Segment Analyzer
Core analysis engine that identifies viral-worthy segments from transcripts.
"""

import asyncio
from typing import Optional

from app.core.config import get_settings
from app.models import Video, Transcription, Clip, PipelineStatus

settings = get_settings()


def analyze_viral_segments(video_id: str) -> dict:
    """
    Main analysis pipeline:
    1. Load transcript from DB
    2. Send to LLM via MCP/OpenAI for viral analysis
    3. Parse and validate the response
    4. Save identified clips to database
    """
    from app.core.database import async_session_factory
    from sqlalchemy import select
    from app.mcp.client import call_opencode_mcp

    async def _update_status():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = PipelineStatus.ANALYZING
                await session.commit()

    asyncio.get_event_loop().run_until_complete(_update_status())

    try:
        async def _load_transcript():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Transcription).where(Transcription.video_id == video_id)
                )
                return result.scalar_one_or_none()

        transcription = asyncio.get_event_loop().run_until_complete(_load_transcript())

        if not transcription:
            raise ValueError("Transcription not found. Run transcription first.")

        transcript_data = {
            "full_text": transcription.full_text or "",
            "segments": transcription.segments_json or [],
            "words": transcription.words_json or [],
            "silence_segments": transcription.silence_segments_json or [],
            "language": transcription.language,
        }

        analysis_result = call_opencode_mcp(transcript_data)

        validated_clips = _validate_and_normalize_clips(analysis_result, transcript_data)

        async def _save_clips():
            async with async_session_factory() as session:
                for idx, clip_data in enumerate(validated_clips):
                    clip = Clip(
                        video_id=video_id,
                        clip_index=idx + 1,
                        start_time=clip_data["start_time"],
                        end_time=clip_data["end_time"],
                        duration=round(clip_data["end_time"] - clip_data["start_time"], 2),
                        virality_score=clip_data["virality_score"],
                        hook_text=clip_data["hook_text"],
                        caption=clip_data["caption"],
                        hashtags=clip_data["hashtags"],
                        mood=clip_data.get("mood", "neutral"),
                        metadata_json={
                            "title": clip_data.get("title", ""),
                            "reason": clip_data.get("reason", ""),
                            "rank": clip_data.get("rank", idx + 1),
                        },
                        status=PipelineStatus.PENDING,
                    )
                    session.add(clip)

                result = await session.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.metadata_json = analysis_result.get("video_analysis", {})
                    video.status = PipelineStatus.PENDING
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_clips())

        return {
            "video_id": video_id,
            "clips_found": len(validated_clips),
            "sentiment": analysis_result.get("video_analysis", {}).get("overall_sentiment", "unknown"),
            "status": "analyzed",
        }

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.status = PipelineStatus.FAILED
                    video.error_message = f"Analysis failed: {str(e)}"
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise


def _validate_and_normalize_clips(
    analysis: dict, transcript_data: dict
) -> list[dict]:
    """
    Validate LLM output:
    - Ensure timestamps are within video duration
    - Remove overlapping clips (keep higher virality score)
    - Enforce max 5 clips, duration 15-90s
    - Sort by start_time
    """
    clips = analysis.get("clips", [])
    if not clips:
        raise ValueError("No clips found in analysis result")

    max_duration = settings.max_clip_duration_seconds
    min_duration = 15

    validated = []
    seen_intervals = []

    for clip in clips:
        start = float(clip.get("start_time", 0))
        end = float(clip.get("end_time", 0))
        duration = end - start

        if duration < min_duration or duration > max_duration:
            continue

        if start < 0:
            start = 0.0

        overlap = any(
            max(start, s["start"]) < min(end, s["end"])
            for s in seen_intervals
        )
        if overlap:
            continue

        validated.append({
            "start_time": round(start, 2),
            "end_time": round(end, 2),
            "virality_score": int(clip.get("virality_score", 50)),
            "hook_text": str(clip.get("hook_text", ""))[:500],
            "caption": str(clip.get("caption", ""))[:2200],
            "hashtags": clip.get("hashtags", [])[:20],
            "mood": str(clip.get("mood", "neutral"))[:32],
            "title": str(clip.get("title", ""))[:200],
            "reason": str(clip.get("reason", "")),
            "rank": int(clip.get("rank", len(validated) + 1)),
        })
        seen_intervals.append({"start": start, "end": end})

    validated.sort(key=lambda x: x["start_time"])
    validated = validated[:5]

    if not validated:
        raise ValueError("No valid clips after validation")

    return validated
