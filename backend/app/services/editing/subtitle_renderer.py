"""
ATELIX ViralClip AI Pipeline — Dynamic Subtitle Renderer
Generates premium Hormozi/TikTok style animated subtitles with active word highlight, uppercase formatting, and stable alignment.
"""

from typing import Optional

MOOD_HIGHLIGHT_COLORS = {
    "inspirational": "&H00FF00&",  # Green
    "humorous": "&H00FF00&",       # Green
    "controversial": "&H0000FF&",  # Red
    "educational": "&H00FFFF&",    # Yellow
    "emotional": "&HFF00FF&",      # Magenta
    "shocking": "&H0080FF&",       # Neon Orange
    "tense": "&H0000FF&",          # Red
    "neutral": "&H00FFFF&",        # Yellow
}

EMOTION_KEYWORDS = {
    "anger": ["benci", "marah", "sakit", "kesal", "jengkel", "hate", "angry", "furious"],
    "excitement": ["luar biasa", "amazing", "gila", "wow", "incredible", "unbelievable", "sains", "moral", "etika"],
    "sadness": ["sedih", "kecewa", "menangis", "cry", "sad", "heartbreaking"],
    "surprise": ["ternyata", "tiba-tiba", "plot twist", "shocking", "surprising"],
    "emphasis": ["sangat", "sekali", "benar-benar", "absolutely", "extremely", "literally", "penting", "utama"],
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
    Returns structured data grouped into display lines.
    """
    # Filter words strictly inside clip range
    clip_words = [
        w for w in words_json
        if w["start"] >= clip_start and w["end"] <= clip_end
    ]

    if not clip_words:
        return []

    # Group into cards of max 2 words for punchy, modern presentation
    lines = _group_words_into_lines(clip_words, max_words_per_line=2)
    subtitle_data = []

    for line_idx, line in enumerate(lines):
        for word in line:
            word_start = word["start"] - clip_start
            word_end = word["end"] - clip_start
            word_text = word["word"].strip()

            is_keyword = False
            keyword_emoji = None

            for emotion, keywords in EMOTION_KEYWORDS.items():
                if word_text.lower() in keywords:
                    is_keyword = True
                    keyword_emoji = EMOTION_EMOJIS.get(emotion)
                    break

            subtitle_data.append({
                "line_index": line_idx,
                "word": word_text,
                "start": round(word_start, 3),
                "end": round(word_end, 3),
                "is_keyword": is_keyword,
                "emoji": keyword_emoji,
            })

    return subtitle_data


def _group_words_into_lines(words: list[dict], max_words_per_line: int = 2) -> list[list[dict]]:
    """
    Group words into display lines (max 2 words per line for clean vertical presentation).
    Splits lines at pauses (>0.3s gap) to prevent visual lingering.
    """
    lines = []
    current_line = []

    for i, word in enumerate(words):
        current_line.append(word)

        if len(current_line) >= max_words_per_line:
            lines.append(current_line)
            current_line = []
            continue

        if i < len(words) - 1:
            gap = words[i + 1]["start"] - word["end"]
            # Split if silence gap is greater than 0.3 seconds
            if gap > 0.3 and len(current_line) >= 1:
                lines.append(current_line)
                current_line = []

    if current_line:
        lines.append(current_line)

    return lines


def generate_ass_subtitle_file(
    subtitle_data: list[dict],
    output_path: str,
    video_width: int = 1080,
    video_height: int = 1920,
    mood: str = "neutral",
) -> str:
    """
    Generate an ASS (Advanced SubStation Alpha) subtitle file.
    Renders lines continuously with color highlighting. Avoids text scaling
    inside the lines to completely eliminate horizontal text shaking (jitter).
    """
    ass_header = f"""[Script Info]
Title: ATELIX ViralClip Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.0,0.0,5,10,10,10,1
"""

    # Group words by line_index
    from collections import defaultdict
    lines_dict = defaultdict(list)
    for item in subtitle_data:
        lines_dict[item["line_index"]].append(item)

    events = []
    highlight_color = MOOD_HIGHLIGHT_COLORS.get(mood, MOOD_HIGHLIGHT_COLORS["neutral"])

    # For each line, schedule dialogue events with gap filling for visual continuity
    for line_idx in sorted(lines_dict.keys()):
        line_words = lines_dict[line_idx]
        if not line_words:
            continue

        # Generate continuous active highlight intervals for each word in the line.
        # Word i's highlight starts exactly at its spoken timestamp, and extends until the next word starts
        # (or the end of the line for the last word) to keep the text visible continuously.
        for active_idx, active_word in enumerate(line_words):
            start_sec = active_word["start"]
            
            # If there is a next word in this line, extend the current word's event duration to the start of the next word.
            # This fills the visual silence gaps cleanly without delaying or pre-highlighting the next word.
            if active_idx < len(line_words) - 1:
                end_sec = line_words[active_idx + 1]["start"]
            else:
                # Last word: highlight stays active until the word ends
                end_sec = active_word["end"]

            start = _seconds_to_ass_time(start_sec)
            end = _seconds_to_ass_time(end_sec)

            # Construct the line text where only the active word is highlighted
            line_parts = []
            for j, w_item in enumerate(line_words):
                w_text = w_item["word"].strip().upper()
                is_kw = w_item.get("is_keyword", False)
                emoji = w_item.get("emoji")
                
                if emoji:
                    w_text = f"{emoji}{w_text}"

                if j == active_idx:
                    color = highlight_color
                else:
                    color = "&H0080FF&" if is_kw else "&HFFFFFF&"

                line_parts.append(
                    f"{{\\c{color}}}{w_text}{{\\c&HFFFFFF&}}"
                )

            text_content = " ".join(line_parts)
            
            # Pop transition (scale 90% -> 100% in 100ms) applied ONLY on the first word of the line card
            anim_tag = "{\\fscx90\\fscy90\\t(0,100,\\fscx100\\fscy100)}" if active_idx == 0 else ""

            # Position at the center horizontally, and lower-middle vertically (y = 1500)
            events.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\an5}}{anim_tag}{{\\pos({video_width // 2},1500)}}{text_content}"
            )

    ass_content = ass_header + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(events)

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
