"""
ATELIX ViralClip AI Pipeline — Celery Worker Tasks
Defines all async background tasks for the full pipeline.
"""

import uuid
from datetime import datetime

from celery import chain, group, chord

from app.core.celery_app import celery_app
from app.models import PipelineStatus


@celery_app.task(bind=True, name="run_full_pipeline")
def run_full_pipeline(self, video_id: str, youtube_url: str):
    """
    Orchestrate the complete pipeline: download → transcribe → analyze → edit → render
    Returns the video_id for monitoring.
    """
    workflow = chain(
        download_video.s(video_id, youtube_url),
        transcribe_audio.s(video_id),
        analyze_virality.s(video_id),
        edit_clips.s(video_id),
        render_clips.s(video_id),
    )

    result = workflow.apply_async()
    return {"video_id": video_id, "chain_id": result.id}


@celery_app.task(bind=True, name="download_video")
def download_video(self, video_id: str, youtube_url: str):
    from app.services.ingestion.downloader import download_youtube_video
    return download_youtube_video(video_id, youtube_url)


@celery_app.task(bind=True, name="transcribe_audio")
def transcribe_audio(self, video_id: str):
    from app.services.ingestion.transcriber import transcribe_with_whisper
    return transcribe_with_whisper(video_id)


@celery_app.task(bind=True, name="analyze_virality")
def analyze_virality(self, video_id: str):
    from app.services.analysis.viral_analyzer import analyze_viral_segments
    return analyze_viral_segments(video_id)


@celery_app.task(bind=True, name="edit_clips")
def edit_clips(self, video_id: str):
    from app.services.editing.video_composer import edit_viral_clips
    return edit_viral_clips(video_id)


@celery_app.task(bind=True, name="render_clips")
def render_clips(self, video_id: str):
    from app.services.editing.video_composer import render_viral_clips
    return render_viral_clips(video_id)


@celery_app.task(bind=True, name="publish_clip_to_tiktok")
def publish_clip_to_tiktok(
    self, clip_id: str, output_path: str, caption: str, hashtags: list
):
    from app.services.publishing.tiktok_bot import publish_to_tiktok
    return publish_to_tiktok(clip_id, output_path, caption, hashtags)
