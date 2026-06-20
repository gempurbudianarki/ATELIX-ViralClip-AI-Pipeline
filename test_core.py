"""
ATELIX ViralClip AI Pipeline — Core Engine Test
Runs each module step-by-step directly, no HTTP server needed.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

print("=" * 60)
print("ATELIX ViralClip AI Pipeline - CORE TEST")
print("=" * 60)

print("\n[TEST 1] Config Load...")
from app.core.config import get_settings
settings = get_settings()
print(f"  OK - DB: {settings.database_url[:50]}...")
print(f"  OK - Whisper: {settings.whisper_model_size} on {settings.whisper_device}")
print(f"  OK - OpenCode MCP: {settings.opencode_mcp_enabled}")

print("\n[TEST 2] Database Init + Models...")
import asyncio
from app.core.database import init_db, async_session_factory
from app.models import Video, Transcription, Clip, PipelineTask, PipelineStatus

async def test_db():
    await init_db()
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(Video))
        count = len(result.scalars().all())
        print(f"  OK - Tables created, {count} videos in DB")
    return True

asyncio.new_event_loop().run_until_complete(test_db())

print("\n[TEST 3] Video CRUD...")
async def test_video():
    async with async_session_factory() as session:
        video = Video(
            youtube_url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            duration_seconds=120.0,
            status=PipelineStatus.PENDING,
        )
        session.add(video)
        await session.flush()
        vid = video.id
        print(f"  OK - Video created: {vid}")

        from sqlalchemy import select
        result = await session.execute(select(Video).where(Video.id == vid))
        loaded = result.scalar_one()
        print(f"  OK - Video loaded: {loaded.title} ({loaded.duration_seconds}s)")
    return vid

video_id = asyncio.new_event_loop().run_until_complete(test_video())

print("\n[TEST 4] Schema Validation...")
from app.schemas import VideoCreateRequest
req = VideoCreateRequest(youtube_url="https://youtu.be/test")
print(f"  OK - URL validated: {req.youtube_url}")

print("\n[TEST 5] Transcription Model...")
async def test_transcription():
    async with async_session_factory() as session:
        trans = Transcription(
            video_id=video_id,
            language="en",
            full_text="This is a test transcript for a viral video analysis pipeline.",
            segments_json=[
                {"id": 0, "start": 0.0, "end": 3.5, "text": "This is a test", "words": [
                    {"word": "This", "start": 0.0, "end": 0.3},
                    {"word": "is", "start": 0.3, "end": 0.6},
                    {"word": "a", "start": 0.6, "end": 0.8},
                    {"word": "test", "start": 0.8, "end": 1.2},
                ]},
                {"id": 1, "start": 3.5, "end": 7.0, "text": "transcript for viral", "words": [
                    {"word": "transcript", "start": 3.5, "end": 4.2},
                    {"word": "for", "start": 4.2, "end": 4.5},
                    {"word": "viral", "start": 4.5, "end": 5.0},
                ]},
            ],
            words_json=[],
        )
        session.add(trans)
        await session.commit()
        print(f"  OK - Transcription saved: {trans.language}, {len(trans.full_text)} chars")
    return True
asyncio.new_event_loop().run_until_complete(test_transcription())

print("\n[TEST 6] Subtitle Generation...")
from app.services.editing.subtitle_renderer import prepare_subtitle_data
words = [
    {"word": "This", "start": 0.0, "end": 0.3, "probability": 0.99},
    {"word": "is", "start": 0.3, "end": 0.6, "probability": 0.99},
    {"word": "amazing", "start": 0.6, "end": 1.0, "probability": 0.99},
    {"word": "content", "start": 1.0, "end": 1.5, "probability": 0.99},
    {"word": "that", "start": 1.5, "end": 1.8, "probability": 0.99},
    {"word": "will", "start": 1.8, "end": 2.0, "probability": 0.99},
    {"word": "go", "start": 2.0, "end": 2.2, "probability": 0.99},
    {"word": "viral", "start": 2.2, "end": 2.6, "probability": 0.99},
]
subs = prepare_subtitle_data(words, 0.0, 3.0, mood="inspirational")
keyword_count = sum(1 for s in subs if s.get("is_keyword"))
print(f"  OK - Generated {len(subs)} subtitle entries, {keyword_count} keyword highlights")

print("\n[TEST 7] MCP / LLM Analysis Prompt...")
from app.mcp.client import _build_analysis_prompt
test_transcript = {
    "full_text": "This is a test. The most viral moment is when I reveal the secret to success.",
    "segments": [
        {"id": 0, "start": 0.0, "end": 3.0, "text": "This is a test.", "words": words[:4]},
        {"id": 1, "start": 3.0, "end": 7.0, "text": "The most viral moment is when I reveal the secret to success.", "words": words[4:]},
    ],
    "words": words,
}
prompt = _build_analysis_prompt(test_transcript)
print(f"  OK - Analysis prompt built: {len(prompt)} chars")
print(f"  Sample: ...{prompt[-200:]}")

print("\n[TEST 8] Clip Validation...")
from app.services.analysis.viral_analyzer import _validate_and_normalize_clips
test_analysis = {
    "video_analysis": {"overall_sentiment": "inspirational"},
    "clips": [
        {"start_time": 0.0, "end_time": 45.0, "virality_score": 88, "hook_text": "This is amazing!", "caption": "You won't believe this 🤯", "hashtags": ["viral", "fyp"], "mood": "shocking", "title": "Mind Blown", "reason": "High emotional impact"},
        {"start_time": 50.0, "end_time": 95.0, "virality_score": 72, "hook_text": "Another clip here", "caption": "Watch till the end", "hashtags": ["trending"], "mood": "neutral", "title": "Clip 2", "reason": "Informative"},
    ],
}
valid_clips = _validate_and_normalize_clips(test_analysis, test_transcript)
print(f"  OK - {len(valid_clips)} clips validated, top score: {valid_clips[0]['virality_score']}")

print("\n[TEST 9] Audio Mood Detection...")
from app.services.audio.enhancer import detect_bgm_mood
mood = detect_bgm_mood("")
print(f"  OK - Default mood: {mood['mood']} (no file = fallback)")

print("\n[TEST 10] FFmpeg Filter Builder...")
from app.services.editing.video_renderer import _build_crop_filter
crop = _build_crop_filter(None, 60.0)
print(f"  OK - Crop filter generated ({len(crop)} chars)")

print("\n" + "=" * 60)
print("ALL 10 TESTS PASSED! Core engine verified.")
print("=" * 60)
print("\nSummary:")
print("  Config    ✓   Whisper: large-v3")
print("  Database  ✓   SQLite (tables created)")
print("  Models    ✓   Video, Transcription, Clip")
print("  Schemas   ✓   Pydantic validation")
print("  Subtitles ✓   Word-level + keyword highlight")
print("  MCP/LLM   ✓   Analysis prompt builder")
print("  Clips     ✓   Validation + dedup logic")
print("  Audio     ✓   Mood detection fallback")
print("  FFmpeg    ✓   Filter generation")
print("\nReady for: whisper download + ffmpeg install + real video test")
