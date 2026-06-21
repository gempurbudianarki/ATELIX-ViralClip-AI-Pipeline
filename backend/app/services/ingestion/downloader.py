"""
ATELIX ViralClip AI Pipeline — YouTube Video Downloader
Downloads video + audio in best quality using yt-dlp.
"""

import os
from pathlib import Path

from app.core.config import get_settings
from app.models import Video, PipelineStatus

settings = get_settings()


def download_youtube_video(video_id: str, youtube_url: str) -> dict:
    """
    Download YouTube video in best quality (video + audio merged).
    Uses yt-dlp with optimal format selection for video editing pipeline.
    """
    from app.core.database import async_session_factory
    from sqlalchemy import select
    import asyncio
    import yt_dlp

    async def _update_status():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if video:
                video.status = PipelineStatus.DOWNLOADING
                await session.commit()

    asyncio.get_event_loop().run_until_complete(_update_status())

    temp_dir = settings.temp_path / video_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(temp_dir / "%(title)s.%(ext)s")

    ffmpeg_dir = str(Path(settings.ffmpeg_binary).parent)

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "ffmpeg_location": ffmpeg_dir,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "getcomments": True,
        "max_comments": 150,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_title = info.get("title", "unknown")
            duration = info.get("duration", 0)
            resolution = info.get("resolution", "unknown")
            comments = info.get("comments", []) or []
            
            cleaned_comments = []
            for c in comments:
                cleaned_comments.append({
                    "text": c.get("text", "") or "",
                    "like_count": c.get("like_count", 0) or 0,
                    "timestamp": c.get("timestamp", 0) or 0,
                })

            if duration > settings.max_video_duration_seconds:
                raise ValueError(
                    f"Video terlalu panjang: {duration}s. Maksimum: {settings.max_video_duration_seconds}s"
                )

            ydl.download([youtube_url])

        downloaded_files = list(temp_dir.glob("*"))
        video_file = None
        for f in downloaded_files:
            if f.suffix in (".mp4", ".mkv", ".webm"):
                video_file = str(f)
                break

        if not video_file:
            raise FileNotFoundError("Video file not found after download")

        async def _save_metadata():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.title = video_title
                    video.duration_seconds = duration
                    video.resolution = resolution or "unknown"
                    video.file_path = video_file
                    video.status = PipelineStatus.PENDING
                    video.metadata_json = {
                        **(video.metadata_json or {}),
                        "comments": cleaned_comments,
                    }
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_metadata())

        return {
            "video_id": video_id,
            "file_path": video_file,
            "title": video_title,
            "duration_seconds": duration,
            "temp_dir": str(temp_dir),
            "status": "downloaded",
        }

    except Exception as e:
        async def _save_error():
            async with async_session_factory() as session:
                result = await session.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.status = PipelineStatus.FAILED
                    video.error_message = str(e)
                    await session.commit()

        asyncio.get_event_loop().run_until_complete(_save_error())
        raise
