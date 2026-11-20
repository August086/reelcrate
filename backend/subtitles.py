from __future__ import annotations

import html
import re
from dataclasses import dataclass

TIMESTAMP_RE = re.compile(
    r"(?:(?P<h>\d{1,2}):)?(?P<m>\d{1,2}):(?P<s>\d{1,2})(?:[.,](?P<ms>\d{1,3}))?"
)
TAG_RE = re.compile(r"<[^>]+>")

LANGUAGE_NAMES = {
    "zh": "中文",
    "zh-cn": "简体中文",
    "zh-hans": "简体中文",
    "zh-tw": "繁体中文",
    "zh-hant": "繁体中文",
    "zh-hk": "繁体中文（香港）",
    "en": "English",
    "en-us": "English (US)",
    "en-gb": "English (UK)",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "ru": "Русский",
    "pt": "Português",
    "it": "Italiano",
    "ar": "العربية",
    "hi": "हिन्दी",
    "th": "ไทย",
    "vi": "Tiếng Việt",
    "id": "Bahasa Indonesia",
    "tr": "Türkçe",
    "pl": "Polski",
    "nl": "Nederlands",
}

PREFERRED_LANGUAGES = [
    "zh-hans",
    "zh-cn",
    "zh",
    "zh-hant",
    "zh-tw",
    "zh-hk",
    "en",
    "en-us",
    "en-gb",
    "ja",
    "ko",
]


@dataclass
class Segment:
    start: float
    end: float
    text: str

    def as_dict(self) -> dict:
        return {"start": round(self.start, 3), "end": round(self.end, 3), "text": self.text}


def parse_timestamp(value: str) -> float:
    match = TIMESTAMP_RE.search(value.strip())
    if not match:
        return 0.0
    hours = int(match.group("h") or 0)
    minutes = int(match.group("m") or 0)
    seconds = int(match.group("s") or 0)
    millis_raw = match.group("ms") or "0"
    millis = int(millis_raw.ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def format_timestamp(seconds: float, *, millis: bool = False) -> str:
    seconds = max(0.0, float(seconds or 0))
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    if millis:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def clean_subtitle_text(text: str) -> str:
    text = html.unescape(text or "")
    text = TAG_RE.sub("", text)
    text = text.replace("&nbsp;", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _timing_line(line: str) -> tuple[float, float] | None:
    if "-->" not in line:
        return None
    left, right = line.split("-->", 1)
    right = right.strip().split(" ")[0]
    return parse_timestamp(left), parse_timestamp(right)


def parse_vtt(text: str) -> list[Segment]:
    text = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    segments: list[Segment] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        timing = _timing_line(line)
        if timing is None:
            index += 1
            continue
        start, end = timing
        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index].strip():
            body.append(clean_subtitle_text(lines[index]))
            index += 1
        content = " ".join(part for part in body if part).strip()
        if content and (not segments or segments[-1].text != content):
            segments.append(Segment(start, end, content))
    return segments


def parse_srt(text: str) -> list[Segment]:
    text = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    segments: list[Segment] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.isdigit():
            index += 1
            continue
        timing = _timing_line(line)
        if timing is None:
            index += 1
            continue
        start, end = timing
        index += 1
        body: list[str] = []
        while index < len(lines) and lines[index].strip():
            body.append(clean_subtitle_text(lines[index]))
            index += 1
        content = " ".join(part for part in body if part).strip()
        if content and (not segments or segments[-1].text != content):
            segments.append(Segment(start, end, content))
    return segments


def parse_bilibili_subtitle(payload: dict) -> list[Segment]:
    segments: list[Segment] = []
    for item in (payload or {}).get("body") or []:
        content = clean_subtitle_text(str(item.get("content") or ""))
        if not content:
            continue
        start = float(item.get("from") or 0)
        end = float(item.get("to") or start)
        if segments and segments[-1].text == content:
            segments[-1].end = max(segments[-1].end, end)
            continue
        segments.append(Segment(start, end, content))
    return segments


def parse_json3(payload: dict) -> list[Segment]:
    segments: list[Segment] = []
    for event in (payload or {}).get("events") or []:
        segs = event.get("segs") or []
        text = clean_subtitle_text("".join(str(seg.get("utf8") or "") for seg in segs))
        if not text:
            continue
        start = float(event.get("tStartMs") or 0) / 1000
        end = start + float(event.get("dDurationMs") or 0) / 1000
        if segments and segments[-1].text == text:
            segments[-1].end = max(segments[-1].end, end)
            continue
        segments.append(Segment(start, end, text))
    return segments


def parse_subtitle_text(text: str, ext: str | None = None) -> list[Segment]:
    lower = (ext or "").lower().lstrip(".")
    if lower == "srt":
        return parse_srt(text)
    if lower in {"json", "json3"}:
        import json

        try:
            return parse_json3(json.loads(text))
        except (TypeError, ValueError):
            return []
    return parse_vtt(text)


def pick_language(available: list[str], requested: str | None = None) -> str | None:
    if not available:
        return None
    lowered = {code.lower(): code for code in available}
    if requested:
        requested_lower = requested.lower()
        for code, original in lowered.items():
            if code == requested_lower:
                return original
    for preferred in PREFERRED_LANGUAGES:
        if preferred in lowered:
            return lowered[preferred]
        for code, original in lowered.items():
            if code.startswith(preferred + "-"):
                return original
    return available[0]


def language_name(code: str) -> str:
    lower = (code or "").lower()
    if lower in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[lower]
    base = lower.split("-")[0]
    return LANGUAGE_NAMES.get(base, code or "未知语言")


def transcript_from_segments(
    segments: list[Segment],
    *,
    max_chars: int = 40000,
    with_timestamps: bool = True,
) -> tuple[str, bool]:
    lines = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        if with_timestamps:
            lines.append(f"[{format_timestamp(segment.start)}] {text}")
        else:
            lines.append(text)
    full = "\n".join(lines)
    if len(full) <= max_chars:
        return full, False

    head_budget = int(max_chars * 0.72)
    tail_budget = max_chars - head_budget - 40
    head: list[str] = []
    size = 0
    for line in lines:
        if size + len(line) + 1 > head_budget:
            break
        head.append(line)
        size += len(line) + 1
    tail: list[str] = []
    size = 0
    for line in reversed(lines):
        if size + len(line) + 1 > tail_budget:
            break
        tail.append(line)
        size += len(line) + 1
    tail.reverse()
    return "\n".join(head + ["[……中间字幕已省略……]"] + tail), True
