"""
ATELIX ViralClip AI Pipeline — FFmpeg Video Renderer
Produces the final 9:16 vertical video with all effects applied.
Uses 2-pass rendering to avoid filter_complex path escaping issues.
"""

import subprocess
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
    source_path: str = "",
    face_data: Optional[dict] = None,
    subtitle_data: Optional[list] = None,
    mood: str = "neutral",
) -> dict:
    """
    Render a single clip with FFmpeg applying:
    1. Smart 9:16 crop centered on face (or frame center)
    2. Dynamic subtitle burn-in from ASS file (2nd pass)
    3. Subtle zoom retention effects
    4. Voice EQ, noise reduction and audio normalisation (audio enhancement)

    Uses 2-pass approach when subtitles are enabled to avoid
    FFmpeg filter_complex path escaping issues on Windows.
    """

    if not source_path:
        raise FileNotFoundError(f"No source_path provided for video_id={video_id}")
    if not Path(source_path).exists():
        raise FileNotFoundError(f"Source video not found: {source_path}")

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
            mood=mood,
        )

    zoom_filter = _build_zoom_filter(duration)

    # Cleanly combine filters so that crop maps to zoom, which then maps to [vout]
    if zoom_filter:
        crop_base = crop_filter.replace("[vout]", "")
        filter_complex = f"{crop_base},{zoom_filter}[vout]"
    else:
        filter_complex = crop_filter

    temp_output = None
    if subtitle_path and Path(subtitle_path).exists():
        temp_output = str(output_dir / f"{Path(output_path).stem}_temp.mp4")
        render_target = temp_output
    else:
        render_target = str(output_path)

    # Fetch professional voice quality audio enhancement filters
    from app.services.audio.enhancer import get_audio_filter_string
    audio_filter_str = get_audio_filter_string(noise_reduction=True, eq_preset="voice")

    cmd_pass1 = [
        settings.ffmpeg_binary,
        "-y",
        "-ss", str(start_time),
        "-i", str(source_path),
        "-t", str(duration),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a",
        "-af", audio_filter_str,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
        render_target,
    ]

    result = subprocess.run(
        cmd_pass1,
        capture_output=True,
        text=True,
        timeout=600,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg render failed for clip {clip_id}: {result.stderr[:2000]}"
        )

    if temp_output and subtitle_path and Path(subtitle_path).exists():
        # Escape Windows path characters for subtitles filter parsing: replace "\" with "/" and escape ":"
        escaped_subtitle_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
        cmd_pass2 = [
            settings.ffmpeg_binary,
            "-y",
            "-i", temp_output,
            "-vf", f"subtitles='{escaped_subtitle_path}'",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]

        result2 = subprocess.run(
            cmd_pass2,
            capture_output=True,
            text=True,
            timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )

        Path(temp_output).unlink(missing_ok=True)

        if result2.returncode != 0:
            raise RuntimeError(
                f"FFmpeg subtitle burn failed for clip {clip_id}: {result2.stderr[:2000]}"
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
    return (
        f"zoompan=z='min(zoom+0.0005,1.05)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
    )
