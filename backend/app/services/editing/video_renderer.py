"""
ATELIX ViralClip AI Pipeline — FFmpeg Video Renderer
Produces the final 9:16 vertical video with all effects applied.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def render_single_clip(
    video_id: str,
    clip_id: str,
    start_time: float,
    end_time: float,
    output_path: str,
    face_data: Optional[dict] = None,
    subtitle_data: Optional[list] = None,
    mood: str = "neutral",
) -> dict:
    """
    Render a single clip with FFmpeg applying:
    1. Smart 9:16 crop centered on face (or frame center)
    2. Dynamic subtitle burn-in from ASS file
    3. Subtle zoom retention effects
    4. Audio pass-through (high quality)
    """

    from app.core.database import async_session_factory
    from app.models import Video
    from sqlalchemy import select
    import asyncio

    async def _get_source_path():
        async with async_session_factory() as session:
            result = await session.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            return video.file_path if video else None

    source_path = asyncio.get_event_loop().run_until_complete(_get_source_path())

    if not source_path:
        raise FileNotFoundError(f"Source video not found for video_id={video_id}")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    duration = end_time - start_time

    crop_filter = _build_crop_filter(
        face_data,
        duration,
        1080,
        1920,
    )

    subtitle_path = None
    if subtitle_data:
        from app.services.editing.subtitle_renderer import generate_ass_subtitle_file

        subtitle_path = str(output_dir / f"{Path(output_path).stem}_subtitles.ass")
        generate_ass_subtitle_file(
            subtitle_data,
            subtitle_path,
            video_width=1080,
            video_height=1920,
        )

    zoom_filter = _build_zoom_filter(duration)

    filter_complex = crop_filter
    if zoom_filter:
        filter_complex = f"{crop_filter},{zoom_filter}"

    cmd = [
        settings.ffmpeg_binary,
        "-y",
        "-ss", str(start_time),
        "-i", str(source_path),
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
    ]

    if subtitle_path and Path(subtitle_path).exists():
        cmd.extend(["-vf", f"ass={subtitle_path}"])

    cmd.append(str(output_path))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg render failed for clip {clip_id}: {result.stderr[:500]}"
        )

    output_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0

    return {
        "clip_id": clip_id,
        "output_path": output_path,
        "duration": round(duration, 2),
        "file_size_bytes": output_size,
        "file_size_mb": round(output_size / (1024 * 1024), 2),
        "resolution": "1080x1920",
        "fps": 30,
    }


def _build_crop_filter(
    face_data: Optional[dict],
    duration: float,
    target_w: int = 1080,
    target_h: int = 1920,
) -> str:
    """
    Build FFmpeg crop + scale filter for smart 9:16 conversion.

    If face tracking data is available, center on the face position.
    Otherwise, center-crop the frame.
    """
    aspect_ratio = target_w / target_h

    if face_data and face_data.get("face_detected"):
        avg_cx = float(face_data.get("average_center_x", 0.5))
        avg_cy = float(face_data.get("average_center_y", 0.5))

        crop_expr = (
            f"crop=iw*0.5625:ih:"
            f"(iw-iw*0.5625)*{min(max(avg_cx, 0.2), 0.8)}:"
            f"(ih-ih)*{min(max(avg_cy, 0.2), 0.8)}"
        )
    else:
        crop_expr = (
            f"crop=iw*0.5625:ih:"
            f"(iw-iw*0.5625)/2:"
            f"0"
        )

    return f"[0:v]{crop_expr},scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}[vout]"


def _build_zoom_filter(duration: float, intensity: float = 0.03) -> str:
    """
    Build subtle zoom-in/zoom-out filter for retention.
    Creates a very slow Ken Burns-style zoom.
    """
    return (
        f"zoompan=z='min(zoom+0.0005,1.05)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
    )
