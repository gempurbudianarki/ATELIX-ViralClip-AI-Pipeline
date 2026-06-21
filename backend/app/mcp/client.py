"""
ATELIX ViralClip AI Pipeline — MCP Client for OpenCode Integration
Bridges the pipeline to OpenCode via Model Context Protocol for LLM-based viral analysis.
"""

import json
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

VIRAL_ANALYSIS_PROMPT = """You are ATELIX, the world's top viral content director and TikTok/Reels algorithm expert with over 20 years of experience editing high-performing short-form videos. Your job is to analyze video transcripts and extract the most viral-worthy segments for TikTok, Instagram Reels, and YouTube Shorts.

## Objectives
Extract up to 5 self-contained, high-value clips from the transcript. For each clip, you must identify a strong opening hook, a complete narrative/educational arc, and determine the optimal duration.

## Critical Clipping Guidelines
1. **Value & Substance (Materi Berbobot)**:
   - Identify sections where the speaker delivers a profound insight, a dramatic story, a counterintuitive fact, or high-value advice.
   - Avoid filler text, dry transitions, or segments that lack standalone value.
   - The clip must follow a complete narrative structure: Hook (First 3s) -> Concept Setup -> Climax/Insight -> Resolution/Conclusion.
2. **The 3-Second Hook**:
   - The first 3 seconds must grab attention. The clip must start exactly at a shocking statement, a bold claim, or an intriguing question.
   - The `hook_text` must be the exact words spoken in the first 3 seconds of the clip.
3. **Optimal Dynamic Duration**:
   - Do not cut clips at arbitrary boundaries. Let the narrative flow dictate the duration.
   - Clips should ideally be 30 to 75 seconds long (max 90s) to allow the viewer to understand the point fully without dragging.
4. **Exact Word Alignment**:
   - Specify accurate start and end timestamps. The start and end timestamps should correspond to segment boundaries.

## Output Format (JSON only, no explanation, no markdown fences)
Return a JSON object with this exact structure:
{
  "video_analysis": {
    "overall_sentiment": "inspirational|humorous|controversial|educational|emotional|shocking",
    "speaker_style": "aggressive|calm|passionate|monotone|conversational",
    "primary_topics": ["topic1", "topic2"],
    "recommended_bgm_mood": "upbeat|dark|inspiring|chill|tense|sad"
  },
  "clips": [
    {
      "rank": 1,
      "start_time": 12.5,
      "end_time": 58.2,
      "hook_text": "The exact sentence spoken in the first 3 seconds of the hook",
      "virality_score": 95,
      "caption": "Attention-grabbing caption with relevant emojis to drive user engagement and comments",
      "hashtags": ["#viral", "#fyp", "#relevant"],
      "mood": "educational",
      "title": "Short descriptive clip title",
      "reason": "Why this segment will go viral"
    }
  ]
}
"""


def get_opencode_credentials():
    """
    Attempt to read OpenCode Go API credentials from the system auth.json config.
    Returns (api_key, base_url).
    """
    import json
    from pathlib import Path

    home = Path.home()
    auth_path = home / ".local" / "share" / "opencode" / "auth.json"
    if auth_path.exists():
        try:
            with open(auth_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                go_data = data.get("opencode-go", {})
                key = go_data.get("key")
                if key:
                    return key, "https://opencode.ai/zen/go/v1"
        except Exception:
            pass
    return None, None


def call_opencode_mcp(transcript_data: dict) -> dict:
    """
    Send transcript data to OpenCode for viral analysis.
    First attempts direct API call to OpenCode Go, falls back to OpenAI or rule-based.
    """
    if settings.opencode_mcp_enabled:
        try:
            return _call_via_mcp(transcript_data)
        except Exception as e:
            print(f"Warning: OpenCode Go API call failed: {e}. Falling back...")
            if settings.openai_api_key:
                return _call_via_openai_fallback(transcript_data)
            return _rule_based_analysis(transcript_data)
    elif settings.openai_api_key:
        return _call_via_openai_fallback(transcript_data)
    else:
        return _rule_based_analysis(transcript_data)


def _call_via_mcp(transcript_data: dict) -> dict:
    """
    Call OpenCode Go API directly using the OpenAI SDK.
    """
    api_key, base_url = get_opencode_credentials()
    if not api_key:
        raise RuntimeError("OpenCode Go API key not found in ~/.local/share/opencode/auth.json")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = _build_analysis_prompt(transcript_data)

    max_chars = 120000
    if len(prompt) > max_chars:
        prompt = prompt[:max_chars // 2] + "\n\n[...content truncated...]\n\n" + prompt[-max_chars // 2:]

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role": "system",
                "content": "You are a world-class viral content director. Return ONLY valid JSON, no markdown fences, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenCode Go API")

    return json.loads(content)


def _call_via_openai_fallback(transcript_data: dict) -> dict:
    """
    Fallback to OpenAI API directly when MCP is unavailable.
    """
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = _build_analysis_prompt(transcript_data)

    max_chars = 100000
    if len(prompt) > max_chars:
        prompt = prompt[:max_chars // 2] + "\n\n[...content truncated...]\n\n" + prompt[-max_chars // 2:]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a world-class viral content director. Return ONLY valid JSON, no markdown fences, no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenAI")

    return json.loads(content)


def _build_analysis_prompt(transcript_data: dict) -> str:
    """
    Build the full analysis prompt with transcript data embedded.
    Converts segment breakdown into logical paragraph blocks with timestamps to enhance LLM context flow.
    """
    segments = transcript_data.get("segments", [])
    comments = transcript_data.get("comments", []) or []

    # Format segment list into clean, readable logical paragraphs with timestamp markers
    timeline_text = ""
    current_paragraph = []
    para_start = 0.0

    for idx, seg in enumerate(segments):
        if not current_paragraph:
            para_start = seg["start"]
        current_paragraph.append(seg["text"])

        # Group adjacent segments to keep logical blocks of around ~15-20 seconds or max 3 segments
        if len(current_paragraph) >= 3 or (seg["end"] - para_start) >= 20.0 or idx == len(segments) - 1:
            para_text = " ".join(current_paragraph).strip()
            timeline_text += f"[{para_start:.1f}s - {seg['end']:.1f}s] {para_text}\n\n"
            current_paragraph = []

    comments_text = ""
    if comments:
        comments_text += "\n### Viewer Comments / Highlights Request\n"
        # Sort comments by like_count desc
        sorted_comments = sorted(comments, key=lambda x: x.get("like_count", 0) or 0, reverse=True)[:20]
        for idx, c in enumerate(sorted_comments):
            comments_text += f"- Comment {idx+1} (likes: {c.get('like_count', 0)}): {c.get('text')}\n"

    prompt = f"""{VIRAL_ANALYSIS_PROMPT}

## Transcript Data (Time-Anchored)
{timeline_text}
{comments_text}

## Instructions
Analyze the transcript above and return the JSON output as specified. Focus on extracting high-value clips with strong hooks and logical story arcs.
"""

    return prompt


def _parse_comment_timestamps(comments: list[dict]) -> dict[int, int]:
    import re
    timestamp_weights = {}
    pattern = re.compile(r'(?:(\d{1,2}):)?(\d{2}):(\d{2})')
    
    for comment in comments:
        text = comment.get("text", "") or ""
        likes = comment.get("like_count", 0) or 0
        weight = 1 + likes
        
        matches = pattern.findall(text)
        for match in matches:
            hours_str, minutes_str, seconds_str = match
            try:
                hours = int(hours_str) if hours_str else 0
                minutes = int(minutes_str)
                seconds = int(seconds_str)
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                safe_weight = min(weight, 50)
                
                # Boost range is total_seconds - 20s to total_seconds + 20s
                for t in range(max(0, total_seconds - 20), total_seconds + 20):
                    timestamp_weights[t] = timestamp_weights.get(t, 0) + safe_weight
            except ValueError:
                continue
                
    return timestamp_weights


def _parse_comment_keywords(comments: list[dict]) -> set[str]:
    import re
    words = []
    stopwords = {
        "yg", "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan", "adalah", 
        "ia", "kami", "mereka", "dia", "saya", "kamu", "bisa", "ada", "tidak", "akan", "pada", 
        "juga", "atau", "ya", "saja", "tapi", "lagi", "kalau", "lu", "gua", "gw",
        "the", "and", "to", "of", "in", "is", "it", "you", "that", "this", "for", "on", "with"
    }
    for comment in comments:
        text = comment.get("text", "").lower() if comment.get("text") else ""
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        for w in cleaned.split():
            if len(w) > 2 and w not in stopwords:
                words.append(w)
                
    from collections import Counter
    counts = Counter(words)
    return set(w for w, c in counts.most_common(20))


def _rule_based_analysis(transcript_data: dict) -> dict:
    """
    Rule-based viral moment detection when no LLM is available.
    
    Strategy:
    1. Group segments into chunks of ~30-45 seconds
    2. Score chunks by word density and completeness
    3. Analyze viewer comments for timestamps and keywords to boost matching chunks
    4. Pick top 5 chunks and construct clips of valid duration (>15s)
    """
    segments = transcript_data.get("segments", [])
    full_text = transcript_data.get("full_text", "")
    comments = transcript_data.get("comments", []) or []

    if not segments:
        return _build_single_clip_response(transcript_data)

    # Parse comments for timestamps and keywords
    timestamp_weights = _parse_comment_timestamps(comments)
    comment_keywords = _parse_comment_keywords(comments)

    # 1. Group adjacent segments into chunks of 15s to 60s
    chunks = []
    current_chunk_segs = []
    current_duration = 0.0

    for seg in segments:
        duration = seg["end"] - seg["start"]
        if duration <= 0:
            continue
        
        current_chunk_segs.append(seg)
        current_duration += duration
        
        if current_duration >= 35.0:
            chunks.append(current_chunk_segs)
            current_chunk_segs = []
            current_duration = 0.0
            
    if current_chunk_segs:
        chunks.append(current_chunk_segs)

    # 2. Score each chunk
    scored_chunks = []
    for idx, chunk in enumerate(chunks):
        if not chunk:
            continue
        start_time = chunk[0]["start"]
        end_time = chunk[-1]["end"]
        chunk_duration = end_time - start_time
        
        if chunk_duration < 15.0:
            # If the last chunk is too short, merge it with previous if possible
            if scored_chunks:
                prev = scored_chunks[-1]
                if (end_time - prev["start"]) <= 90.0:
                    prev["end"] = end_time
                    prev["text"] += " " + " ".join(s.get("text", "") for s in chunk)
                    prev["word_count"] += sum(len(s.get("words", [])) for s in chunk)
                    prev["score"] = (prev["score"] + 50) / 2
                    continue
            continue

        text = " ".join(s.get("text", "") for s in chunk)
        word_count = sum(len(s.get("words", [])) for s in chunk)
        density = word_count / chunk_duration if chunk_duration > 0 else 0
        
        completeness = 2.0 if text.strip() and text.strip()[-1] in ".!?" else 1.0
        excitement = 0.0
        for s in chunk:
            for w in s.get("words", []):
                word_text = w.get("word", "").lower()
                if word_text in {"amazing", "incredible", "unbelievable", "wow", "never", "secret", "shocking"}:
                    excitement += 0.3
                    
        # Calculate comment timestamp weight in this chunk
        chunk_comments_weight = 0
        for t in range(int(start_time), int(end_time) + 1):
            chunk_comments_weight += timestamp_weights.get(t, 0)
            
        # Boost score based on comment timestamps
        boost_multiplier = 1.0
        if chunk_comments_weight > 0:
            boost_multiplier = 1.0 + min(chunk_comments_weight / 100.0, 0.8)

        # Check comment keywords matches
        keyword_matches = 0
        for w in comment_keywords:
            if w in text.lower():
                keyword_matches += 1
        
        keyword_boost = min(keyword_matches * 1.5, 6.0)
                    
        score = (density * 10 + completeness + excitement + keyword_boost) * boost_multiplier
        scored_chunks.append({
            "start": start_time,
            "end": end_time,
            "text": text,
            "score": round(min(score, 100), 1),
            "word_count": word_count,
        })

    # 3. Sort by score and take top 5
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:5]

    sentiment = _guess_sentiment(full_text)

    clips = []
    for i, chunk in enumerate(top_chunks):
        hook = chunk["text"][:120] if chunk["text"] else ""
        hashtags = _generate_hashtags(chunk["text"], sentiment)

        clips.append({
            "rank": i + 1,
            "start_time": round(chunk["start"], 2),
            "end_time": round(chunk["end"], 2),
            "virality_score": int(chunk["score"]),
            "hook_text": hook,
            "caption": f"{chunk['text'][:200]} {' '.join('#' + h for h in hashtags[:3])}",
            "hashtags": hashtags,
            "mood": sentiment,
            "title": chunk["text"][:60] if chunk["text"] else f"Clip {i + 1}",
            "reason": f"Word density: {chunk['score']:.1f}, {chunk['word_count']} words, {chunk['end'] - chunk['start']:.1f}s",
        })

    clips.sort(key=lambda x: x["start_time"])

    return {
        "video_analysis": {
            "overall_sentiment": sentiment,
            "speaker_style": "conversational",
            "primary_topics": [],
            "recommended_bgm_mood": "neutral",
        },
        "clips": clips if clips else _default_clips(transcript_data),
    }


def _build_single_clip_response(transcript_data: dict) -> dict:
    """Fallback: make one clip from the entire transcript."""
    words = transcript_data.get("words", [])
    if not words:
        return {
            "video_analysis": {"overall_sentiment": "neutral"},
            "clips": [],
        }

    start = words[0]["start"]
    end = words[-1]["end"]
    full_text = transcript_data.get("full_text", "")

    return {
        "video_analysis": {
            "overall_sentiment": "neutral",
            "speaker_style": "conversational",
        },
        "clips": [{
            "rank": 1,
            "start_time": round(start, 2),
            "end_time": round(end, 2),
            "virality_score": 50,
            "hook_text": full_text[:120],
            "caption": full_text[:200],
            "hashtags": ["fyp", "viral"],
            "mood": "neutral",
            "title": "Full Clip",
            "reason": "Single segment fallback — no transcript segments detected",
        }],
    }


def _guess_sentiment(text: str) -> str:
    """Quick sentiment guess based on keyword presence."""
    t = text.lower()
    positive = sum(1 for w in ["amazing", "great", "awesome", "love", "best", "incredible", "cool"] if w in t)
    negative = sum(1 for w in ["hate", "terrible", "worst", "bad", "awful", "sad"] if w in t)
    question = sum(1 for w in ["what", "how", "why", "secret", "truth", "revealed"] if w in t)

    if question > positive:
        return "educational"
    if positive > negative + 1:
        return "inspirational"
    if negative > positive:
        return "controversial"
    return "neutral"


def _generate_hashtags(text: str, sentiment: str) -> list[str]:
    """Generate basic hashtags from text keywords and sentiment."""
    tags = []
    t = text.lower()

    keyword_map = {
        "ai": "ai", "artificial": "ai",
        "money": "money", "rich": "wealth",
        "secret": "secrets", "truth": "truth",
        "life": "lifehack", "hack": "lifehack",
        "love": "love",
        "science": "science", "tech": "technology",
        "future": "future",
    }

    for key, tag in keyword_map.items():
        if key in t and tag not in tags:
            tags.append(tag)

    if len(tags) < 3:
        tags.extend(["viral", "fyp"])

    sentiment_tags = {
        "inspirational": "motivation",
        "humorous": "comedy",
        "controversial": "debate",
        "educational": "learnontiktok",
        "emotional": "feelings",
        "shocking": "wow",
    }
    mood_tag = sentiment_tags.get(sentiment)
    if mood_tag and mood_tag not in tags:
        tags.append(mood_tag)

    return tags[:8]


def _default_clips(transcript_data: dict) -> list[dict]:
    """Fallback clips when scoring produces nothing."""
    full_text = transcript_data.get("full_text", "")
    words = transcript_data.get("words", [])
    if not words:
        return []
    start = words[0]["start"]
    end = words[-1]["end"]
    return [{
        "rank": 1,
        "start_time": round(start, 2),
        "end_time": round(end, 2),
        "virality_score": 40,
        "hook_text": full_text[:120] if full_text else "",
        "caption": (full_text or "")[:200],
        "hashtags": ["viral", "fyp"],
        "mood": "neutral",
        "title": "Full Video",
        "reason": "Rule-based fallback",
    }]
