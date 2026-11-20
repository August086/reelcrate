from __future__ import annotations

import logging
import re
import threading
import time
import urllib.parse
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

import requests
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

from bilibili import bili_client, is_bilibili_url
from config import settings
from errors import AppError, NoSubtitlesError, UnsupportedURLError
from media import ensure_file, ffmpeg_path
from schemas import DirectURLData, FormatOption, SubtitleLanguage, SubtitlePayload, SubtitleSegment, VideoInfo
from subtitles import (
    language_name,
    parse_subtitle_text,
    parse_vtt,
    pick_language,
    transcript_from_segments,
)
from url_guard import normalize_and_validate, safe_filename

log = logging.getLogger("reelcrate.downloader")

PLATFORM_NAMES = {
    "youtube": "YouTube",
    "youtube:tab": "YouTube",
    "bilibili": "哔哩哔哩",
    "ted": "TED",
    "tedtalk": "TED",
    "tiktok": "TikTok",
    "douyin": "抖音",
    "twitter": "X / Twitter",
    "instagram": "Instagram",
    "vimeo": "Vimeo",
    "facebook": "Facebook",
    "twitch": "Twitch",
    "generic": "网页视频",
}
FORCE_PROXY_KEYS = {"youtube", "youtube:tab", "bilibili"}
SUBTITLE_EXTS = ("vtt", "srt", "json3", "json")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class TTLCache:
    def __init__(self, ttl: int, max_items: int = 100) -> None:
        self.ttl = ttl
        self.max_items = max_items
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            expires, value = item
            if expires <= now:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._items[key] = (time.time() + self.ttl, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


info_cache = TTLCache(settings.info_cache_ttl, 120)
raw_cache = TTLCache(min(settings.info_cache_ttl, 300), 20)


def _ydl_opts(download: bool = False) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "skip_download": not download,
        "socket_timeout": 25,
        "retries": 3,
        "extractor_retries": 2,
        "http_headers": {
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
        },
    }
    ffmpeg = ffmpeg_path()
    if ffmpeg:
        options["ffmpeg_location"] = ffmpeg
    cookie_file = (getattr(settings, "ytdlp_cookiefile", "") or "").strip()
    if cookie_file:
        options["cookiefile"] = cookie_file
    return options


def _clean_error(message: str) -> str:
    text = ANSI_RE.sub("", str(message or "")).strip()
    text = re.sub(r"^ERROR:\s*", "", text)
    text = re.sub(r"^\[[^\]]+\]\s*[^:]+:\s*", "", text)
    return text[:500] or "解析失败，请稍后重试。"


def _extract_raw(url: str, *, fresh: bool = False) -> dict[str, Any]:
    if not fresh:
        cached = raw_cache.get(url)
        if cached is not None:
            return cached
    try:
        with yt_dlp.YoutubeDL(_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
    except (DownloadError, ExtractorError) as exc:
        message = _clean_error(str(exc))
        lowered = message.lower()
        if "unsupported url" in lowered or "no video formats" in lowered:
            raise UnsupportedURLError("该链接暂不支持，请换一个视频链接。") from exc
        if "private" in lowered or "login" in lowered or "sign in" in lowered:
            raise AppError(f"该视频需要登录才能解析：{message}", code="login_required", status_code=422) from exc
        raise AppError(f"解析失败：{message}", code="extract_failed", status_code=422) from exc
    except Exception as exc:
        log.exception("yt-dlp extraction crashed")
        raise AppError("解析服务暂时不可用，请稍后重试。", code="extract_failed", status_code=502) from exc

    if not info:
        raise UnsupportedURLError("没有解析到视频信息。")
    if info.get("_type") == "playlist" or info.get("entries"):
        raise UnsupportedURLError("暂不支持播放列表或合集，请粘贴单个视频链接。")
    if info.get("is_live"):
        raise AppError("暂不支持直播流，请等待直播结束后再试。", code="live_unsupported", status_code=422)
    raw_cache.set(url, info)
    return info


def _platform_key(info: dict[str, Any]) -> str:
    key = str(info.get("extractor_key") or info.get("extractor") or "generic").lower()
    if key.startswith("youtube"):
        return "youtube"
    if key.startswith("ted"):
        return "ted"
    return key


def _platform_name(info: dict[str, Any], key: str) -> str:
    if key in PLATFORM_NAMES:
        return PLATFORM_NAMES[key]
    raw = str(info.get("extractor_key") or info.get("extractor") or "网页视频")
    return raw.replace("_", " ")


def _int_or_none(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _duration_string(duration: int | None) -> str | None:
    if not duration:
        return None
    hours, remainder = divmod(int(duration), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def _format_size(fmt: dict[str, Any] | None, duration: int | None = None) -> int | None:
    if not fmt:
        return None
    known = _int_or_none(fmt.get("filesize")) or _int_or_none(fmt.get("filesize_approx"))
    if known:
        return known
    if not duration:
        return None
    try:
        bitrate = float(fmt.get("tbr") or fmt.get("abr") or 0)
    except (TypeError, ValueError):
        bitrate = 0.0
    if bitrate <= 0:
        return None
    return int(bitrate * duration * 1000 / 8)


def _height_label(height: int | None) -> str:
    if not height:
        return "最佳"
    if height >= 2160:
        return "4K"
    if height >= 1440:
        return "2K"
    if height >= 1080:
        return "1080P"
    if height >= 720:
        return "720P"
    if height >= 480:
        return "480P"
    if height >= 360:
        return "360P"
    return f"{height}P"


def _candidate_score(fmt: dict[str, Any]) -> tuple[int, float]:
    score = 0
    ext = str(fmt.get("ext") or "").lower()
    vcodec = str(fmt.get("vcodec") or "").lower()
    acodec = str(fmt.get("acodec") or "").lower()
    if ext == "mp4":
        score += 4
    if vcodec.startswith(("avc", "h264")):
        score += 3
    if acodec and acodec != "none":
        score += 1
    try:
        tbr = float(fmt.get("tbr") or 0)
    except (TypeError, ValueError):
        tbr = 0.0
    return score, tbr


def _video_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    formats = info.get("formats") or []
    usable = []
    for fmt in formats:
        if not isinstance(fmt, dict):
            continue
        if str(fmt.get("vcodec") or "none").lower() == "none":
            continue
        if not fmt.get("height"):
            continue
        if not fmt.get("url"):
            continue
        usable.append(fmt)
    return usable


def _build_formats(info: dict[str, Any], duration: int | None) -> list[FormatOption]:
    videos = _video_formats(info)
    audio_formats = [
        fmt
        for fmt in info.get("formats") or []
        if isinstance(fmt, dict)
        and str(fmt.get("acodec") or "none").lower() != "none"
        and str(fmt.get("vcodec") or "none").lower() == "none"
    ]
    best_audio = max(
        audio_formats,
        key=lambda item: float(item.get("tbr") or item.get("abr") or 0),
        default=None,
    )
    audio_size = _format_size(best_audio, duration)
    audio_ext = str((best_audio or {}).get("ext") or "m4a")

    by_height: dict[int, dict[str, Any]] = {}
    for fmt in videos:
        height = int(fmt.get("height") or 0)
        if not height:
            continue
        current = by_height.get(height)
        if current is None or _candidate_score(fmt) > _candidate_score(current):
            by_height[height] = fmt

    options: list[FormatOption] = []
    for height in sorted(by_height, reverse=True)[:10]:
        candidate = by_height[height]
        size = _format_size(candidate, duration)
        progressive = str(candidate.get("acodec") or "none").lower() != "none"
        if not progressive and audio_size:
            size = (size or 0) + audio_size if size else None
        label = _height_label(height)
        codec = str(candidate.get("vcodec") or "").split(".")[0]
        quality = codec.upper() if codec and codec != "none" else "视频"
        options.append(
            FormatOption(
                id=f"yt-video-{height}",
                label=label,
                quality=quality,
                height=height,
                ext="mp4",
                filesize=size,
                kind="video",
                recommended=False,
                needs_merge=not progressive,
                note="自动合并音视频" if not progressive else "单文件",
            )
        )
    if options:
        options[0].recommended = True
    elif info.get("url"):
        options.append(
            FormatOption(
                id="yt-video-best",
                label="最佳",
                quality="原始画质",
                height=_int_or_none(info.get("height")),
                ext=str(info.get("ext") or "mp4"),
                filesize=_int_or_none(info.get("filesize")),
                kind="video",
                recommended=True,
                needs_merge=False,
                note="单文件",
            )
        )

    if best_audio:
        options.append(
            FormatOption(
                id="yt-audio",
                label="仅音频",
                quality=f"{audio_ext.upper()} 音频",
                ext="mp3",
                filesize=audio_size,
                kind="audio",
                needs_merge=False,
                note="转码为 MP3",
            )
        )
    return options


def _subtitle_languages(info: dict[str, Any]) -> list[SubtitleLanguage]:
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    result: list[SubtitleLanguage] = []
    seen: set[str] = set()
    for code in manual:
        if code in {"live_chat", "comments"} or code in seen:
            continue
        seen.add(code)
        result.append(SubtitleLanguage(code=str(code), name=language_name(str(code))))
    for code in auto:
        if code in {"live_chat", "comments"} or code in seen:
            continue
        seen.add(code)
        result.append(SubtitleLanguage(code=str(code), name=f"{language_name(str(code))}（自动）"))
    order = {code: index for index, code in enumerate(["zh-hans", "zh-cn", "zh", "zh-hant", "zh-tw", "en", "ja", "ko"])}
    result.sort(key=lambda item: order.get(item.code.lower(), 99))
    return result


def _to_video_info(url: str, info: dict[str, Any]) -> VideoInfo:
    key = _platform_key(info)
    duration = _int_or_none(info.get("duration"))
    thumbnail = info.get("thumbnail")
    if not thumbnail:
        thumbs = info.get("thumbnails") or []
        if thumbs and isinstance(thumbs[-1], dict):
            thumbnail = thumbs[-1].get("url")
    if isinstance(thumbnail, str) and thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[7:]
    upload_date = info.get("upload_date")
    if isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit():
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    formats = _build_formats(info, duration)
    if not formats:
        raise UnsupportedURLError("没有找到可下载的视频格式。")
    webpage = str(info.get("webpage_url") or url)
    notes: list[str] = []
    if key == "youtube":
        notes.append("YouTube 需要可访问的视频网络环境；部分视频还要求登录 Cookie。")
    return VideoInfo(
        id=str(info.get("id") or "video"),
        title=str(info.get("title") or "未命名视频").strip(),
        thumbnail=str(thumbnail) if thumbnail else None,
        duration=duration,
        duration_string=_duration_string(duration),
        uploader=str(info.get("uploader") or info.get("channel") or "").strip() or None,
        platform=_platform_name(info, key),
        platform_key=key,
        view_count=_int_or_none(info.get("view_count")),
        upload_date=upload_date if isinstance(upload_date, str) else None,
        webpage_url=webpage,
        formats=formats,
        subtitles=_subtitle_languages(info),
        source="ytdlp",
        notes=notes,
    )


def parse_video(url: str) -> VideoInfo:
    normalized = normalize_and_validate(url)
    cached = info_cache.get(normalized)
    if cached is not None:
        return cached
    if is_bilibili_url(normalized):
        info, _ = bili_client.parse(normalized)
        info_cache.set(normalized, info)
        return info
    raw = _extract_raw(normalized)
    info = _to_video_info(normalized, raw)
    info_cache.set(normalized, info)
    return info


def _subtitle_entry(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not entries:
        return None
    for ext in SUBTITLE_EXTS:
        for entry in entries:
            if str(entry.get("ext") or "").lower() == ext and entry.get("url"):
                return entry
    return next((entry for entry in entries if entry.get("url")), None)


def _parse_hls_subtitles(playlist_url: str, headers: dict[str, str]) -> list:
    from concurrent.futures import ThreadPoolExecutor

    from subtitles import Segment

    try:
        response = requests.get(playlist_url, headers=headers, timeout=40)
        response.raise_for_status()
    except Exception as exc:
        raise NoSubtitlesError("字幕播放列表下载失败，请稍后再试。") from exc
    lines = response.text.replace("\r\n", "\n").split("\n")
    entries: list[tuple[float, str]] = []
    duration = 0.0
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            try:
                duration = float(line.split(":", 1)[1].split(",", 1)[0])
            except (TypeError, ValueError):
                duration = 0.0
        elif line and not line.startswith("#"):
            entries.append((duration, urljoin(playlist_url, line)))
    if not entries:
        return []

    def fetch(segment_url: str) -> str | None:
        try:
            segment_response = requests.get(segment_url, headers=headers, timeout=25)
            segment_response.raise_for_status()
            return segment_response.text
        except Exception:
            return None

    urls = [entry[1] for entry in entries]
    with ThreadPoolExecutor(max_workers=8) as executor:
        texts = list(executor.map(fetch, urls))

    merged: dict[tuple[float, str], Segment] = {}
    cursor = 0.0
    for (segment_duration, _), segment_text in zip(entries, texts):
        if segment_text is None:
            cursor += segment_duration
            continue
        for segment in parse_vtt(segment_text):
            start = segment.start
            end = segment.end
            # HLS subtitle segments may carry absolute or segment-relative timestamps.
            if start + 8 < cursor:
                start += cursor
                end += cursor
            if start + 4 < cursor:
                start = cursor
            if end <= start:
                continue
            key = (round(start, 2), segment.text)
            existing = merged.get(key)
            if existing is None:
                merged[key] = Segment(start, end, segment.text)
            else:
                existing.end = max(existing.end, end)
        cursor += segment_duration
    result: list = []
    for item in sorted(merged.values(), key=lambda segment: segment.start):
        if result and result[-1].text == item.text:
            result[-1].end = max(result[-1].end, item.end)
            continue
        result.append(item)
    return result


def _fetch_subtitles(url: str, language: str | None) -> SubtitlePayload:
    raw = _extract_raw(url)
    manual = raw.get("subtitles") or {}
    auto = raw.get("automatic_captions") or {}
    available = [str(code) for code in manual] + [str(code) for code in auto if code not in manual]
    code = pick_language(available, language)
    if not code:
        raise NoSubtitlesError()
    from_manual = code in manual
    entries = manual.get(code) if from_manual else auto.get(code)
    entry = _subtitle_entry(entries or [])
    if not entry or not entry.get("url"):
        raise NoSubtitlesError("该视频没有可直接下载的字幕。")
    headers = dict(raw.get("http_headers") or {})
    headers.setdefault("User-Agent", USER_AGENT)
    headers.setdefault("Referer", str(raw.get("webpage_url") or url))
    try:
        response = requests.get(entry["url"], headers=headers, timeout=40)
        response.raise_for_status()
        text = response.text
    except Exception as exc:
        raise NoSubtitlesError("字幕下载失败，请稍后再试。") from exc
    if text.lstrip().startswith("#EXTM3U"):
        segments = _parse_hls_subtitles(str(entry["url"]), headers)
    else:
        segments = parse_subtitle_text(text, str(entry.get("ext") or "vtt"))
    if not segments:
        raise NoSubtitlesError("字幕内容为空，无法生成 AI 总结。")
    transcript, truncated = transcript_from_segments(segments, max_chars=40000)
    platform = _platform_name(raw, _platform_key(raw))
    return SubtitlePayload(
        language=code,
        language_name=language_name(code),
        source=f"{platform} {'人工字幕' if from_manual else '自动字幕'}",
        segments=[SubtitleSegment(**segment.as_dict()) for segment in segments],
        full_text=transcript,
        truncated=truncated,
    )


def get_subtitles(url: str, language: str | None = None) -> SubtitlePayload:
    normalized = normalize_and_validate(url)
    if is_bilibili_url(normalized):
        return bili_client.get_subtitles(normalized, language)
    return _fetch_subtitles(normalized, language)


def _download_ytdlp(
    url: str,
    option_id: str,
    job_dir: Path,
    progress: Callable[[float, str], None],
    max_bytes: int,
) -> tuple[Path, str, str]:
    raw = _extract_raw(url, fresh=True)
    duration = _int_or_none(raw.get("duration"))
    is_audio = option_id == "yt-audio"
    selector_height: int | None = None
    if option_id.startswith("yt-video-") and option_id.split("-")[-1].isdigit():
        selector_height = int(option_id.split("-")[-1])

    outtmpl = str(job_dir / "media.%(ext)s")

    def hook(data: dict[str, Any]) -> None:
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes") or 0
            if total:
                pct = min(92.0, 2.0 + (float(downloaded) / float(total)) * 88.0)
                progress(pct, "正在下载")
            else:
                progress(5, "正在下载")
        elif status == "finished":
            progress(93, "正在合并 / 转码")

    options = _ydl_opts(download=True)
    options.update(
        {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "max_filesize": max_bytes,
            "progress_hooks": [hook],
            "merge_output_format": "mp4",
        }
    )
    if is_audio:
        options["format"] = "bestaudio/best"
        options["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    elif selector_height:
        options["format"] = (
            f"bestvideo[height<={selector_height}]+bestaudio/"
            f"best[height<={selector_height}]"
        )
    else:
        options["format"] = "bestvideo+bestaudio/best"

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
    except DownloadError as exc:
        raise AppError(f"下载失败：{_clean_error(str(exc))}", code="download_failed", status_code=422) from exc
    except Exception as exc:
        log.exception("yt-dlp download crashed")
        raise AppError("下载服务异常，请稍后重试。", code="download_failed", status_code=502) from exc

    candidates = [
        path
        for path in job_dir.glob("media.*")
        if path.is_file() and not path.name.endswith((".part", ".ytdl"))
    ]
    if not candidates:
        raise AppError("下载完成但没有找到文件，请重试。", code="file_missing", status_code=500)
    if is_audio:
        target = next((path for path in candidates if path.suffix.lower() == ".mp3"), None)
    else:
        target = next((path for path in candidates if path.suffix.lower() == ".mp4"), None)
    target = target or max(candidates, key=lambda path: path.stat().st_mtime)
    size = ensure_file(str(target))
    if size > max_bytes:
        target.unlink(missing_ok=True)
        raise AppError("文件超过大小限制，已取消。", code="file_too_large", status_code=413)
    ext = target.suffix.lstrip(".").lower() or ("mp3" if is_audio else "mp4")
    filename = safe_filename(str(raw.get("title") or "video"), ext)
    final_path = job_dir / filename
    if final_path.resolve() != target.resolve():
        target.replace(final_path)
    progress(100, "下载完成")
    return final_path, ext, filename


def download_video(
    url: str,
    option_id: str,
    job_dir: Path,
    progress: Callable[[float, str], None],
    max_bytes: int,
) -> tuple[Path, str, str]:
    normalized = normalize_and_validate(url)
    job_dir.mkdir(parents=True, exist_ok=True)
    if is_bilibili_url(normalized):
        return bili_client.download(normalized, option_id, job_dir, progress, max_bytes)
    return _download_ytdlp(normalized, option_id, job_dir, progress, max_bytes)


def get_direct_url(url: str, option_id: str | None = None) -> DirectURLData:
    normalized = normalize_and_validate(url)
    if is_bilibili_url(normalized):
        raise AppError(
            "B 站视频需要服务端合并音视频，请使用代理下载。",
            code="direct_unavailable",
            status_code=409,
        )
    raw = _extract_raw(normalized, fresh=True)
    key = _platform_key(raw)
    if key in FORCE_PROXY_KEYS:
        raise AppError(
            "该平台直链需要特殊请求头或会快速过期，请使用代理下载。",
            code="direct_unavailable",
            status_code=409,
        )

    is_audio = option_id == "yt-audio"
    height: int | None = None
    if option_id and option_id.startswith("yt-video-") and option_id.split("-")[-1].isdigit():
        height = int(option_id.split("-")[-1])
    formats = raw.get("formats") or []
    candidates: list[dict[str, Any]] = []
    for fmt in formats:
        if not isinstance(fmt, dict) or not fmt.get("url"):
            continue
        vcodec = str(fmt.get("vcodec") or "none").lower()
        acodec = str(fmt.get("acodec") or "none").lower()
        if is_audio:
            if vcodec != "none" or acodec == "none":
                continue
        else:
            if vcodec == "none" or acodec == "none":
                continue
            if height and int(fmt.get("height") or 0) > height:
                continue
        candidates.append(fmt)
    if not candidates and not is_audio and raw.get("url") and str(raw.get("ext") or "") in {"mp4", "webm", "mov", "m4v"}:
        candidates.append(
            {
                "url": raw["url"],
                "ext": raw.get("ext"),
                "height": raw.get("height"),
                "tbr": raw.get("tbr"),
            }
        )
    if not candidates:
        raise AppError(
            "该清晰度没有单文件直链，请使用代理下载（服务端会自动合并）。",
            code="direct_unavailable",
            status_code=409,
        )
    candidates.sort(
        key=lambda fmt: (
            int(fmt.get("height") or 0) if not is_audio else float(fmt.get("abr") or 0),
            _candidate_score(fmt)[1],
        ),
        reverse=True,
    )
    chosen = candidates[0]
    direct_url = str(chosen["url"])
    headers = dict(raw.get("http_headers") or {})
    headers.setdefault("User-Agent", USER_AGENT)
    try:
        with requests.get(
            direct_url,
            headers={**headers, "Range": "bytes=0-1"},
            stream=True,
            timeout=20,
            allow_redirects=True,
        ) as response:
            content_type = str(response.headers.get("Content-Type") or "").lower()
            if response.status_code not in (200, 206) or "text/html" in content_type:
                raise AppError("直链校验失败，请使用代理下载。", code="direct_unavailable", status_code=409)
            next(response.iter_content(2), b"")
    except AppError:
        raise
    except Exception as exc:
        raise AppError("直链暂时不可用，请使用代理下载。", code="direct_unavailable", status_code=409) from exc

    ext = str(chosen.get("ext") or ("mp3" if is_audio else "mp4"))
    filename = safe_filename(str(raw.get("title") or "video"), ext)
    return DirectURLData(
        direct_url=direct_url,
        filename=filename,
        ext=ext,
        filesize=_format_size(chosen, _int_or_none(raw.get("duration"))),
    )
