"""
ATELIX ViralClip AI Pipeline — End-to-End Test
Download short YouTube video, transcribe, analyze, edit, render.
"""
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, ".")
import nest_asyncio
nest_asyncio.apply()

print("=" * 60)
print("ATELIX ViralClip AI — END-TO-END TEST")
print("=" * 60)

# Load config
from app.core.config import get_settings
settings = get_settings()

# Test video (short ~1 min for quick test)
YOUTUBE_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

print(f"\n[1/5] Checking video metadata...")
import yt_dlp
ydl_opts = {"quiet": True, "no_warnings": True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(YOUTUBE_URL, download=False)
    title = info["title"]
    duration = info["duration"]
    print(f"  Title: {title}")
    print(f"  Duration: {duration}s ({duration // 60}:{duration % 60:02d})")

print(f"\n[2/5] Downloading video...")
from app.services.ingestion.downloader import download_youtube_video
import uuid
video_id = str(uuid.uuid4())

# Create Video record in DB first (like the API does)
import asyncio
from app.core.database import async_session_factory
from app.models import Video, PipelineStatus

async def create_video_record():
    async with async_session_factory() as session:
        video = Video(
            id=video_id,
            youtube_url=YOUTUBE_URL,
            status=PipelineStatus.PENDING,
        )
        session.add(video)
        await session.commit()
    print(f"  Video record created: {video_id}")

asyncio.get_event_loop().run_until_complete(create_video_record())
try:
    result = download_youtube_video(video_id, YOUTUBE_URL)
    print(f"  Downloaded: {result['file_path']}")
    print(f"  Duration: {result['duration_seconds']}s")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

print(f"\n[3/5] Transcribing with Whisper...")
from app.services.ingestion.transcriber import transcribe_with_whisper
try:
    result = transcribe_with_whisper(video_id)
    print(f"  Language: {result['language']}")
    print(f"  Segments: {result['segments_count']}")
    print(f"  Words: {result['words_count']}")
    print(f"  Speech: {result['speech_duration']}s")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

print(f"\n[4/5] Analyzing virality (AI Director)...")
print("  Sending transcript to AI for viral moment analysis...")
from app.services.analysis.viral_analyzer import analyze_viral_segments
try:
    result = analyze_viral_segments(video_id)
    print(f"  Clips found: {result['clips_found']}")
    print(f"  Sentiment: {result['sentiment']}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"\n[5/5] Rendering clips...")
from app.services.editing.video_composer import edit_viral_clips, render_viral_clips
try:
    edit_result = edit_viral_clips(video_id)
    print(f"  Clips prepared: {edit_result['clips_prepared']}")
except Exception as e:
    print(f"  Edit phase error: {e}")

try:
    render_result = render_viral_clips(video_id)
    print(f"  Total: {render_result['total_clips']}")
    print(f"  Rendered: {render_result['rendered']}")
    print(f"  Failed: {render_result['failed']}")
except Exception as e:
    print(f"  Render phase error: {e}")

print("\n" + "=" * 60)
print("END-TO-END TEST COMPLETED!")
print("=" * 60)
