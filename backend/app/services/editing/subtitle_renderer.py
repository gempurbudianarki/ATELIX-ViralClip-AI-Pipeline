"""
ATELIX ViralClip AI Pipeline — Dynamic Subtitle Renderer
Generates Hormozi-style word-level animated subtitles with keyword highlighting and emoji insertion.
"""

from typing import Optional

MOOD_COLORS = {
    "inspirational": {"primary": "#FFD700", "secondary": "#FFFFFF", "highlight": "#FF6B35"},
    "humorous": {"primary": "#00FF88", "secondary": "#FFFFFF", "highlight": "#FF3366"},
    "controversial": {"primary": "#FF4444", "secondary": "#FFFFFF", "highlight": "#FF0000"},
    "educational": {"primary": "#4FC3F7", "secondary": "#FFFFFF", "highlight": "#FFA726"},
    "emotional": {"primary": "#FF80AB", "secondary": "#FFFFFF", "highlight": "#E040FB"},
    "shocking": {"primary": "#FF1744", "secondary": "#FFD600", "highlight": "#FF9100"},
    "tense": {"primary": "#B71C1C", "secondary": "#FFFFFF", "highlight": "#FF3D00"},
    "neutral": {"primary": "#FFFFFF", "secondary": "#CCCCCC", "highlight": "#00E5FF"},
}

EMOTION_KEYWORDS = {
    "anger": ["benci", "marah", "sakit", "kesal", "jengkel", "hate", "angry", "furious"],
    "excitement": ["luar biasa", "amazing", "gila", "wow", "incredible", "unbelievable"],
    "sadness": ["sedih", "kecewa", "menangis", "cry", "sad", "heartbreaking"],
    "surprise": ["ternyata", "tiba-tiba", "plot twist", "shocking", "surprising"],
    "emphasis": ["sangat", "sekali", "benar-benar", "absolutely", "extremely", "literally"],
    "negation": ["tidak", "bukan", "jangan", "never", "don't", "won't", "can't"],
}

EMOTION_EMOJIS = {
    "anger": "😡",
    "excitement": "🔥",
    "sadness": "😢",
    "surprise": "😱",
    "emphasis": "💯",
    "negation": "❌",
}


def prepare_subtitle_data(
    words_json: list[dict],
    clip_start: float,
    clip_end: float,
    mood: str = "neutral",
) -> list[dict]:
    """
    Prepare word-level subtitle data for the given clip time range.
    Returns structured data for FFmpeg drawtext filter rendering.

    Each word gets:
    - Timestamp relative to clip start
    - Color based on mood and keyword detection
    - Animation flag for word-level highlighting
    - Emoji insertion points before/after emotional keywords
    """
    clip_words = [
        w for w in words_json
        if w["start"] >= clip_start and w["end"] <= clip_end
    ]

    if not clip_words:
        return []

    colors = MOOD_COLORS.get(mood, MOOD_COLORS["neutral"])
    lines = _group_words_into_lines(clip_words, clip_start)
    subtitle_data = []

    for line_idx, line in enumerate(lines):
        for word in line:
            word_start = word["start"] - clip_start
            word_end = word["end"] - clip_start
            word_text = word["word"].strip()

            word_color = colors["secondary"]
            is_keyword = False
            keyword_emoji = None

            for emotion, keywords in EMOTION_KEYWORDS.items():
                if word_text.lower() in keywords:
                    word_color = colors["highlight"]
                    is_keyword = True
                    keyword_emoji = EMOTION_EMOJIS.get(emotion)
                    break

            subtitle_data.append({
                "line_index": line_idx,
                "word": word_text,
                "start": round(word_start, 3),
                "end": round(word_end, 3),
                "color": word_color,
                "is_keyword": is_keyword,
                "emoji": keyword_emoji,
                "font_size": 36 if is_keyword else 32,
            })

    return _add_entry_transitions(subtitle_data)


def _group_words_into_lines(words: list[dict], clip_start: float) -> list[list[dict]]:
    """
    Group words into display lines (max 4-5 words per line).
    Respects natural pauses (>0.3s gap = new line).
    """
    lines = []
    current_line = []
    max_words_per_line = 5

    for i, word in enumerate(words):
        current_line.append(word)

        if len(current_line) >= max_words_per_line:
            lines.append(current_line)
            current_line = []
            continue

        if i < len(words) - 1:
            gap = words[i + 1]["start"] - word["end"]
            if gap > 0.3 and len(current_line) >= 2:
                lines.append(current_line)
                current_line = []

    if current_line:
        lines.append(current_line)

    return lines


def _add_entry_transitions(subtitle_data: list[dict]) -> list[dict]:
    """
    Add animation metadata for word entry/exit transitions.
    Words appear with a slight scale-up effect (100ms).
    """
    for item in subtitle_data:
        item["animation"] = {
            "type": "pop",
            "duration_ms": 100,
            "easing": "ease_out_cubic",
        }

    return subtitle_data


def generate_ass_subtitle_file(
    subtitle_data: list[dict],
    output_path: str,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Generate an ASS (Advanced SubStation Alpha) subtitle file from word-level data.
    This enables FFmpeg to burn subtitles with per-word styling.
    """
    ass_header = f"""[Script Info]
Title: ATELIX ViralClip Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,32,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,80,80,120,1
Style: Highlight,Montserrat,36,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,80,80,120,1
Style: Keyword,Montserrat,36,&H0035FF6B,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,80,80,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    y_positions = {}

    for item in subtitle_data:
        line_idx = item["line_index"]
        if line_idx not in y_positions:
            y_positions[line_idx] = 1400 + line_idx * 80

        start = _seconds_to_ass_time(item["start"])
        end = _seconds_to_ass_time(item["end"])

        style = "Default"
        if item.get("is_keyword"):
            style = "Keyword"
        elif item.get("color") == "#00E5FF":
            style = "Highlight"

        text = item["word"]
        if item.get("emoji"):
            text = f"{item['emoji']} {text}"

        y = y_positions[line_idx]

        events.append(
            f"Dialogue: 0,{start},{end},{style},,0,0,0,,{{\\an5}}{{\\pos({video_width // 2},{y})}}{text}"
        )

    ass_content = ass_header + "\n".join(events)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_path


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
