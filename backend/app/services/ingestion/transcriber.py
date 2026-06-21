"""
ATELIX ViralClip AI Pipeline — Whisper Transcriber
Transcribes audio using faster-whisper with word-level timestamps.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    pass

settings = get_settings()

_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            download_root=str(settings.models_path),
        )
    return _whisper_model


def transcribe_with_whisper(video_id: str) -> dict:
    """
    Run faster-whisper on the audio track of the downloaded video.
    Produces word-level timestamps for precise subtitle rendering.
    Supports language override via video metadata.
    """
    from app.core.database import async_session_factory
    from app.models import Video, Transcription, PipelineStatus
    from sqlalchemy import select

    async def _update_status():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = PipelineStatus.TRANSCRIBING
                await session.commit()

    asyncio.get_event_loop().run_until_complete(_update_status())

    try:
        async def _get_video():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                return video

        video = asyncio.get_event_loop().run_until_complete(_get_video())

        if not video or not video.file_path:
            raise ValueError("Video file not found")

        model = _get_model()

        # Retrieve manual language override from metadata if available
        meta = video.metadata_json or {}
        lang_override = meta.get("language")
        if lang_override == "auto" or not lang_override:
            lang_param = None
        else:
            lang_param = lang_override

        print(f"Starting Whisper transcription for video {video_id} (language parameter: {lang_param})")

        segments_result, info = model.transcribe(
            video.file_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
            language=lang_param,
        )

        segments = []
        words = []
        full_text_parts = []

        for segment in segments_result:
            seg_data = {
                "id": segment.id,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "avg_logprob": round(segment.avg_logprob, 4),
            }

            seg_words = []
            if segment.words:
                for w in segment.words:
                    word_data = {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 4) if w.probability else 1.0,
                    }
                    seg_words.append(word_data)
                    words.append({**word_data, "segment_id": segment.id})

            seg_data["words"] = seg_words
            segments.append(seg_data)
            full_text_parts.append(segment.text.strip())

        speech_duration = sum(s["end"] - s["start"] for s in segments)
        silence_segments = _detect_silence_regions(segments, video.duration_seconds or 0)

        async def _save_transcription():
            async with async_session_factory() as session:
                transcription = Transcription(
                    video_id=video_id,
                    language=info.language,
                    full_text=" ".join(full_text_parts),
                    segments_json=segments,
                    words_json=words,
                    silence_segments_json=silence_segments,
                )
                session.add(transcription)

                result = await session.execute(select(Video).where(Video.id == video_id))
                vid = result.scalar_one_or_none()
                if vid:
                    vid.status = PipelineStatus.PENDING
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_transcription())

        return {
            "video_id": video_id,
            "language": info.language,
            "duration": round(info.duration, 1),
            "segments_count": len(segments),
            "words_count": len(words),
            "full_text_length": len(" ".join(full_text_parts)),
            "speech_duration": round(speech_duration, 1),
            "silence_gaps": len(silence_segments),
            "status": "transcribed",
        }

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                vid = result.scalar_one_or_none()
                if vid:
                    vid.status = PipelineStatus.FAILED
                    vid.error_message = f"Transcription failed: {str(e)}"
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise


def _detect_silence_regions(segments: list, total_duration: float) -> list[dict]:
    """
    Detect gaps between speech segments that are candidates for jump-cut removal.
    Returns list of silence regions with start/end times.
    """
    if not segments:
        return []

    silence_regions = []
    min_gap = 0.15

    if segments[0]["start"] > min_gap:
        silence_regions.append({
            "start": 0.0,
            "end": round(segments[0]["start"], 3),
            "duration": round(segments[0]["start"], 3),
        })

    for i in range(len(segments) - 1):
        gap = segments[i + 1]["start"] - segments[i]["end"]
        if gap > min_gap:
            silence_regions.append({
                "start": round(segments[i]["end"], 3),
                "end": round(segments[i + 1]["start"], 3),
                "duration": round(gap, 3),
            })

    if total_duration > 0 and segments[-1]["end"] < total_duration - min_gap:
        silence_regions.append({
            "start": round(segments[-1]["end"], 3),
            "end": round(total_duration, 3),
            "duration": round(total_duration - segments[-1]["end"], 3),
        })

    return silence_regions
