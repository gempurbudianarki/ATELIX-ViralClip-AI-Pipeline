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

VIRAL_ANALYSIS_PROMPT = """You are ATELIX, the world's top viral content director and TikTok algorithm expert with 20 years of experience. Your job is to analyze video transcripts and identify the most viral-worthy moments for short-form content (TikTok/Reels/Shorts, 9:16 vertical format).

## Your Task
Analyze the provided transcript (with word-level timestamps) and extract the most engaging, shareable, and viral-potential segments.

## Analysis Criteria
For each segment, evaluate:
1. **Hook Potential** (0-10): How strong is the opening? Does it grab attention in the first 1-3 seconds?
2. **Emotional Impact** (0-10): Does it trigger strong emotion (shock, laughter, anger, inspiration, curiosity)?
3. **Shareability** (0-10): Would people send this to friends or repost it?
4. **Controversy/Novelty** (0-10): Is the content surprising, counterintuitive, or debate-sparking?
5. **Completeness** (0-10): Can this segment stand alone as a complete micro-story?

## Output Format (JSON only, no explanation)
Return a JSON object with:
```json
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
      "end_time": 72.3,
      "hook_text": "The exact sentence for the first 3 seconds hook",
      "virality_score": 92,
      "caption": "Attention-grabbing TikTok caption with emojis",
      "hashtags": ["#viral", "#fyp", "#relevant"],
      "mood": "inspirational",
      "title": "Short clip title",
      "reason": "Why this segment will go viral"
    }
  ]
}
```

Rules:
- Maximum 5 clips per video
- Each clip must be 15-90 seconds (ideal: 30-60 seconds)
- Clips must NOT overlap
- Prioritize segments with strong emotional peaks
- Ensure every clip has a complete thought/narrative arc
- The hook_text MUST be the exact words that appear in the first 3 seconds
- Captions must include a call-to-action or question to drive comments
- Hashtags must include 3-5 trending + 2 niche-specific tags
- Timestamps must be accurate based on the word-level data provided
"""


def call_opencode_mcp(transcript_data: dict) -> dict:
    """
    Send transcript data to OpenCode via MCP for viral analysis.
    
    If OpenCode MCP is unavailable, falls back to direct OpenAI API call.
    """
    if settings.opencode_mcp_enabled:
        try:
            return _call_via_mcp(transcript_data)
        except Exception as e:
            if settings.openai_api_key:
                return _call_via_openai_fallback(transcript_data)
            raise RuntimeError(f"MCP call failed and no OpenAI fallback: {e}")
    elif settings.openai_api_key:
        return _call_via_openai_fallback(transcript_data)
    else:
        raise RuntimeError("No LLM backend configured. Set OPENCODE_MCP_ENABLED=true or provide OPENAI_API_KEY.")


def _call_via_mcp(transcript_data: dict) -> dict:
    """
    Call OpenCode via MCP protocol.
    
    Uses the mcp Python SDK to communicate with OpenCode's MCP server.
    """
    import subprocess
    import tempfile
    import json
    import time

    prompt = _build_analysis_prompt(transcript_data)

    prompt_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    try:
        prompt_file.write(prompt)
        prompt_file.close()

        result = subprocess.run(
            [settings.opencode_binary_path, "--prompt-file", prompt_file.name, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(Path.cwd()),
        )

        if result.returncode != 0:
            raise RuntimeError(f"OpenCode exited with code {result.returncode}: {result.stderr}")

        output = result.stdout.strip()
        json_start = output.find("{")
        json_end = output.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(f"No JSON found in OpenCode response: {output[:500]}")

        return json.loads(output[json_start:json_end])

    finally:
        import os
        try:
            os.unlink(prompt_file.name)
        except OSError:
            pass


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
    """
    segments = transcript_data.get("segments", [])
    full_text = transcript_data.get("full_text", "")
    words = transcript_data.get("words", [])

    word_timeline = ""
    for i, word in enumerate(words[:3000]):
        word_timeline += f"[{word['start']:.1f}s] {word['word']}\n"

    segments_text = ""
    for seg in segments[:200]:
        word_list = ", ".join(
            [w["word"] for w in seg.get("words", [])[:30]]
        )
        segments_text += (
            f"Segment {seg['id']}: [{seg['start']:.1f}s - {seg['end']:.1f}s] "
            f"Text: {seg['text']}\n"
        )

    prompt = f"""{VIRAL_ANALYSIS_PROMPT}

## Transcript Data

### Full Transcript
{full_text[:5000]}

### Word-Level Timeline (first 3000 words)
{word_timeline}

### Segment Breakdown (first 200 segments)
{segments_text}

## Instructions
Analyze the transcript above and return the JSON output as specified. Focus on finding the most viral-worthy moments.
"""

    return prompt
