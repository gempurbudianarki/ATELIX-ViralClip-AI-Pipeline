import sys
sys.path.insert(0, "backend")

# Test 6-10 (DB-dependent tests already passed in test_core.py)

from app.services.editing.subtitle_renderer import prepare_subtitle_data
words = [
    {"word": "This", "start": 0.0, "end": 0.3, "probability": 0.99},
    {"word": "is", "start": 0.3, "end": 0.6, "probability": 0.99},
    {"word": "amazing", "start": 0.6, "end": 1.0, "probability": 0.99},
    {"word": "content", "start": 1.0, "end": 1.5, "probability": 0.99},
]
subs = prepare_subtitle_data(words, 0.0, 2.0, mood="inspirational")
kw = sum(1 for s in subs if s.get("is_keyword"))
print(f"[TEST 6] Subtitles: {len(subs)} words, {kw} keywords highlighted")

from app.mcp.client import _build_analysis_prompt
prompt = _build_analysis_prompt({"full_text": "Test.", "segments": [], "words": words})
print(f"[TEST 7] MCP Prompt: {len(prompt)} chars built")

from app.services.analysis.viral_analyzer import _validate_and_normalize_clips
analysis = {
    "video_analysis": {"overall_sentiment": "inspirational"},
    "clips": [
        {"start_time": 0.0, "end_time": 45.0, "virality_score": 88, "hook_text": "Wow!", "caption": "Amazing", "hashtags": ["viral"], "mood": "shocking", "title": "A", "reason": "x"},
        {"start_time": 50.0, "end_time": 95.0, "virality_score": 72, "hook_text": "Hey", "caption": "Cool", "hashtags": ["trending"], "mood": "neutral", "title": "B", "reason": "y"},
    ],
}
valid = _validate_and_normalize_clips(analysis, {"full_text": "test", "segments": [], "words": []})
print(f"[TEST 8] Clip Validation: {len(valid)} valid clips")

from app.services.audio.enhancer import detect_bgm_mood
mood = detect_bgm_mood("")
print(f"[TEST 9] Audio Mood: {mood['mood']} (fallback)")

from app.services.editing.video_renderer import _build_crop_filter
crop = _build_crop_filter(None, 60.0)
print(f"[TEST 10] FFmpeg Filter: {len(crop)} chars")

print("\n" + "=" * 50)
print("TESTS 6-10 PASSED")
print("=" * 50)
