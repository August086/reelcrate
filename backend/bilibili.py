from __future__ import annotations

import hashlib
import re
import threading
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import requests

from config import settings
from errors import AppError, NoSubtitlesError, UnsupportedURLError
from media import ensure_file, merge_audio_video
from schemas import FormatOption, SubtitleLanguage, SubtitlePayload, SubtitleSegment, VideoInfo
from subtitles import (
    Segment,
    language_name,
    parse_bilibili_subtitle,
    pick_language,
    transcript_from_segments,
)
from url_guard import safe_filename, validate_public_url

API_BASE = "https://api.bilibili.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
)
BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
}
SHORT_HOSTS = {"b23.tv", "bili2233.cn", "bili22.cn"}
VIDEO_HOSTS = {"bilibili.com", "www.bilibili.com", "m.bilibili.com"}
BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})", re.I)
AID_RE = re.compile(r"/av(\d+)", re.I)
OPTION_RE = re.compile(r"^bili-(audio|\d+)-(avc|hevc|av1)$", re.I)

WBI_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]
API_MESSAGES = {
    -404: "视频不存在或已被删除。",
    -403: "没有访问该视频的权限。",
    -10403: "该视频存在地区限制或版权限制。",
    62002: "稿件不可见，可能正在审核或已被下架。",
    62004: "稿件正在审核中。",
}


@dataclass
class BiliMeta:
    bvid: str
    aid: int | None
    cid: int
    page: int
    title: str
    duration: int
    thumbnail: str | None
    owner: str
    webpage_url: str


def is_bilibili_url(url: str) -> bool:
    try:
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return False
    return host in SHORT_HOSTS or any(host == h or host.endswith("." + h) for h in VIDEO_HOSTS)


def _is_short(url: str) -> bool:
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower() in SHORT_HOSTS
    except ValueError:
        return False


def _https(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return "https://" + url[7:]
    return url


def _quality_label(height: int | None, qn: int | None = None) -> str:
    if height and height >= 2160:
        return "4K"
    if height and height >= 1440:
        return "2K"
    if height and height >= 1080:
        return "1080P"
    if height and height >= 720:
        return "720P"
    if height and height >= 480:
        return "480P"
    if height and height >= 360:
        return "360P"
    if height:
        return f"{height}P"
    return str(qn or "")


def _codec_family(codecs: str) -> str:
    value = (codecs or "").lower()
    if value.startswith(("avc", "h264")):
        return "avc"
    if value.startswith(("hev", "hvc", "h265")):
        return "hevc"
    if value.startswith("av01"):
        return "av1"
    return (value.split(".")[0] or "codec")[:8]


def _codec_label(family: str) -> str:
    return {"avc": "H.264", "hevc": "HEVC", "av1": "AV1"}.get(family, family.upper())


def _estimate_size(bandwidth: int | None, duration: int | None) -> int | None:
    if not bandwidth or not duration:
        return None
    return int(float(bandwidth) * float(duration) / 8 * 1.04)


def _select_subtitle_item(items: list[dict], requested: str | None = None) -> dict | None:
    if not items:
        return None
    if requested:
        requested_lower = requested.lower()
        for item in items:
            if str(item.get("lan") or "").lower() == requested_lower:
                return item

    def rank(item: dict) -> int:
        code = str(item.get("lan") or "").lower()
        is_ai = code.startswith("ai-")
        if not is_ai and (code == "zh" or code.startswith("zh-")):
            return 0
        if is_ai and (code in {"ai-zh"} or code.startswith("ai-zh-")):
            return 1
        if not is_ai and (code == "en" or code.startswith("en-")):
            return 2
        if not is_ai:
            return 3
        return 4

    return min(items, key=rank)


class BiliClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self._lock = threading.RLock()
        self._bootstrapped = False
        self._wbi_mixin = ""
        self._wbi_at = 0.0

    # ------------------------------------------------------------------ session
    def _bootstrap(self, force: bool = False) -> None:
        with self._lock:
            if self._bootstrapped and not force and (time.time() - self._wbi_at) < 6 * 3600:
                return
            try:
                response = self.session.get(f"{API_BASE}/x/frontend/finger/spi", timeout=20)
                if response.status_code == 412:
                    raise AppError(
                        "B 站接口暂时拦截了当前网络，请稍后重试或配置 BILIBILI_COOKIE。",
                        code="bilibili_blocked",
                        status_code=502,
                    )
                response.raise_for_status()
                data = (response.json() or {}).get("data") or {}
            except AppError:
                raise
            except Exception as exc:
                raise AppError("无法连接 B 站接口，请检查网络。", code="bilibili_network", status_code=502) from exc

            for name, value in (("buvid3", data.get("b_3")), ("buvid4", data.get("b_4"))):
                if value:
                    self.session.cookies.set(name, value, domain=".bilibili.com")
            self.session.cookies.set("b_nut", str(int(time.time())), domain=".bilibili.com")

            cookie_header = (getattr(settings, "bilibili_cookie", "") or "").strip()
            if cookie_header:
                for chunk in cookie_header.split(";"):
                    if "=" in chunk:
                        name, value = chunk.split("=", 1)
                        self.session.cookies.set(name.strip(), value.strip(), domain=".bilibili.com")
            if settings.bilibili_sessdata:
                self.session.cookies.set("SESSDATA", settings.bilibili_sessdata, domain=".bilibili.com")

            try:
                nav = self.session.get(f"{API_BASE}/x/web-interface/nav", timeout=20).json()
                wbi = ((nav or {}).get("data") or {}).get("wbi_img") or {}
                img = (wbi.get("img_url") or "").rsplit("/", 1)[-1].split(".")[0]
                sub = (wbi.get("sub_url") or "").rsplit("/", 1)[-1].split(".")[0]
                raw = img + sub
                if len(raw) >= 64:
                    self._wbi_mixin = "".join(raw[index] for index in WBI_TAB)[:32]
            except Exception:
                # Signing is required; a stale mixin is better than a hard crash only if we had one.
                pass
            if not self._wbi_mixin:
                raise AppError("B 站签名初始化失败，请稍后重试。", code="bilibili_wbi", status_code=502)
            self._bootstrapped = True
            self._wbi_at = time.time()

    def _sign(self, params: dict) -> dict:
        with self._lock:
            self._bootstrap()
            signed = {str(key): str(value) for key, value in params.items()}
            signed["wts"] = str(int(time.time()))
            ordered = {key: signed[key] for key in sorted(signed)}
            query = urllib.parse.urlencode(ordered, safe="")
            ordered["w_rid"] = hashlib.md5((query + self._wbi_mixin).encode("utf-8")).hexdigest()
            return ordered

    def _request(self, path: str, params: dict | None = None, *, signed: bool = False) -> dict:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with self._lock:
                    if signed:
                        query = self._sign(params or {})
                    else:
                        self._bootstrap()
                        query = params or {}
                    response = self.session.get(f"{API_BASE}{path}", params=query, timeout=30)
                if response.status_code == 412:
                    if attempt == 0:
                        self._bootstrap(force=True)
                        continue
                    raise AppError(
                        "B 站接口返回 412，当前网络被临时限制，请稍后再试。",
                        code="bilibili_blocked",
                        status_code=502,
                    )
                if response.status_code >= 500:
                    raise AppError("B 站服务暂时不可用，请稍后再试。", code="bilibili_http", status_code=502)
                if not response.ok:
                    raise AppError(f"B 站接口请求失败（HTTP {response.status_code}）。", code="bilibili_http", status_code=502)
                payload = response.json()
            except AppError as exc:
                last_error = exc
                if exc.code == "bilibili_blocked" and attempt == 0:
                    continue
                raise
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    self._bootstrap(force=True)
                    continue
                raise AppError("B 站接口响应异常，请稍后再试。", code="bilibili_http", status_code=502) from exc

            code = payload.get("code")
            if code == 0:
                return payload.get("data") or {}
            if code in {-403, -352} and signed and attempt == 0:
                self._bootstrap(force=True)
                continue
            message = API_MESSAGES.get(code) or payload.get("message") or "B 站接口返回错误。"
            if code in {-404, -403, -10403, 62002, 62004}:
                raise AppError(str(message), code="bilibili_api", status_code=422)
            raise AppError(f"{message}（错误码 {code}）", code="bilibili_api", status_code=502)
        raise last_error or AppError("B 站接口请求失败。", code="bilibili_http", status_code=502)

    # ------------------------------------------------------------------ parsing
    def _resolve_url(self, url: str) -> str:
        url = validate_public_url(url)
        if _is_short(url):
            try:
                response = requests.get(url, headers=BASE_HEADERS, timeout=20, allow_redirects=True)
                final = response.url
            except Exception as exc:
                raise AppError("短链接解析失败，请展开后粘贴完整链接。", code="bilibili_short_link") from exc
            if not is_bilibili_url(final):
                raise UnsupportedURLError("短链接没有指向 B 站视频。")
            url = validate_public_url(final)
        if not is_bilibili_url(url):
            raise UnsupportedURLError("这不是 B 站视频链接。")
        return url

    def _identifiers(self, url: str) -> tuple[str | None, int | None, int]:
        parts = urllib.parse.urlsplit(url)
        bvid_match = BVID_RE.search(parts.path + "?" + parts.query)
        aid_match = AID_RE.search(parts.path)
        if not bvid_match and not aid_match:
            if any(token in parts.path for token in ("/bangumi/", "/cheese/", "/read/")):
                raise UnsupportedURLError("暂不支持番剧、课程和专栏，请使用普通视频链接。")
            raise UnsupportedURLError("没有识别到 B 站视频 ID，请粘贴 BV 号或 av 号链接。")
        query = urllib.parse.parse_qs(parts.query)
        try:
            page = max(1, int((query.get("p") or ["1"])[0]))
        except (TypeError, ValueError):
            page = 1
        bvid = bvid_match.group(1) if bvid_match else None
        aid = int(aid_match.group(1)) if aid_match else None
        return bvid, aid, page

    def _view(self, bvid: str | None, aid: int | None) -> dict:
        params = {"bvid": bvid} if bvid else {"aid": aid}
        return self._request("/x/web-interface/view", params)

    def _playurl(self, bvid: str | None, aid: int | None, cid: int) -> dict:
        params = {
            "cid": cid,
            "qn": 127,
            "fnver": 0,
            "fnval": 16,
            "fourk": 1,
        }
        if bvid:
            params["bvid"] = bvid
        else:
            params["avid"] = aid
        data = self._request("/x/player/wbi/playurl", params, signed=True)
        if not data.get("dash"):
            # Fall back to the legacy endpoint for very old videos that only expose durl.
            params.update({"qn": 64, "fnval": 1, "fnver": 0})
            data = self._request("/x/player/wbi/playurl", params, signed=True)
        return data

    def _subtitle_languages(self, bvid: str, cid: int) -> list[SubtitleLanguage]:
        try:
            data = self._request("/x/player/wbi/v2", {"bvid": bvid, "cid": cid}, signed=True)
        except AppError:
            return []
        subtitle = (data.get("subtitle") or {}) if isinstance(data, dict) else {}
        items = subtitle.get("subtitles") or []
        result: list[SubtitleLanguage] = []
        seen: set[str] = set()
        for item in items:
            code = str(item.get("lan") or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            name = str(item.get("lan_doc") or "").strip() or language_name(code)
            if str(item.get("lan") or "").startswith("ai-"):
                name = f"{name}（AI）"
            result.append(SubtitleLanguage(code=code, name=name))
        return result

    def _formats(self, playurl: dict, duration: int | None) -> tuple[list[FormatOption], dict]:
        dash = playurl.get("dash") or {}
        accept_quality = playurl.get("accept_quality") or []
        accept_desc = playurl.get("accept_description") or []
        quality_map = {int(q): d for q, d in zip(accept_quality, accept_desc) if str(q).isdigit()}

        grouped: dict[int, dict] = {}
        for item in dash.get("video") or []:
            qn = item.get("id")
            if qn is None:
                continue
            family = _codec_family(str(item.get("codecs") or ""))
            current = grouped.get(int(qn))
            rank = {"avc": 3, "hevc": 2, "av1": 1}.get(family, 0)
            current_rank = {"avc": 3, "hevc": 2, "av1": 1}.get(current.get("family", ""), 0) if current else -1
            if current is None or rank > current_rank:
                grouped[int(qn)] = {"item": item, "family": family}

        audio_items = dash.get("audio") or []
        best_audio = max(audio_items, key=lambda item: int(item.get("bandwidth") or 0), default=None)
        audio_size = _estimate_size(best_audio.get("bandwidth") if best_audio else None, duration)

        formats: list[FormatOption] = []
        for qn in sorted(grouped, key=lambda value: int(grouped[value]["item"].get("height") or 0), reverse=True):
            entry = grouped[qn]
            item = entry["item"]
            family = entry["family"]
            height = int(item.get("height") or 0) or None
            label = _quality_label(height, qn)
            size = _estimate_size(item.get("bandwidth"), duration)
            if size and audio_size:
                size += audio_size
            desc = str(quality_map.get(qn) or "").strip()
            if label and label in desc:
                desc = desc.replace(label, "").strip(" ·")
            quality = f"{desc} · {_codec_label(family)}" if desc else _codec_label(family)
            formats.append(
                FormatOption(
                    id=f"bili-{qn}-{family}",
                    label=label,
                    quality=quality,
                    height=height,
                    ext="mp4",
                    filesize=size,
                    kind="video",
                    recommended=False,
                    needs_merge=True,
                    note="视频 + 音频合并",
                )
            )
        if formats:
            formats[0].recommended = True

        if best_audio:
            formats.append(
                FormatOption(
                    id="bili-audio",
                    label="仅音频",
                    quality="M4A 音频",
                    ext="m4a",
                    filesize=audio_size,
                    kind="audio",
                    needs_merge=False,
                    note="不含视频",
                )
            )
        return formats, {"best_audio": best_audio, "video": grouped, "quality_map": quality_map}

    def parse(self, url: str) -> tuple[VideoInfo, BiliMeta]:
        resolved = self._resolve_url(url)
        bvid, aid, page = self._identifiers(resolved)
        data = self._view(bvid, aid)
        bvid = str(data.get("bvid") or bvid or "")
        aid = int(data.get("aid") or aid or 0) or None
        pages = data.get("pages") or []
        selected_page = page
        if pages:
            selected_page = min(max(1, page), len(pages))
        page_info = pages[selected_page - 1] if pages else {}
        cid = int(page_info.get("cid") or data.get("cid") or 0)
        if not cid:
            raise AppError("无法获取该视频的分 P 信息。", code="bilibili_cid", status_code=422)
        title = str(data.get("title") or "未命名视频").strip()
        part = str(page_info.get("part") or "").strip()
        if len(pages) > 1 and part:
            title = f"{title} · P{selected_page} {part}"
        duration = int(page_info.get("duration") or data.get("duration") or 0) or None
        thumbnail = _https(data.get("pic"))
        owner = str((data.get("owner") or {}).get("name") or "").strip() or None
        pubdate = data.get("pubdate")
        upload_date = None
        if isinstance(pubdate, (int, float)) and pubdate > 0:
            try:
                upload_date = datetime.fromtimestamp(pubdate).strftime("%Y-%m-%d")
            except (OverflowError, OSError, ValueError):
                upload_date = None
        view_count = int((data.get("stat") or {}).get("view") or 0) or None
        webpage_url = f"https://www.bilibili.com/video/{bvid}"
        if selected_page > 1:
            webpage_url += f"?p={selected_page}"

        playurl = self._playurl(bvid or None, aid, cid)
        formats, _ = self._formats(playurl, duration)
        if not formats:
            raise AppError("该视频没有可用的播放流，可能需要登录或版权限制。", code="bilibili_no_stream", status_code=422)
        subtitles = self._subtitle_languages(bvid, cid)

        notes: list[str] = []
        if not settings.bilibili_logged_in:
            notes.append("未登录 B 站：匿名解析通常最高约 480P；配置 BILIBILI_SESSDATA 可解锁更高清晰度与部分 CC 字幕。")
        if playurl.get("accept_quality"):
            notes.append("B 站实际返回的清晰度受账号与视频本身限制，页面仅展示当前可下载的档位。")

        info = VideoInfo(
            id=bvid,
            title=title,
            thumbnail=thumbnail,
            duration=duration,
            duration_string=_duration_string(duration),
            uploader=owner,
            platform="哔哩哔哩",
            platform_key="bilibili",
            view_count=view_count,
            upload_date=upload_date,
            webpage_url=webpage_url,
            formats=formats,
            subtitles=subtitles,
            source="bilibili",
            notes=notes,
        )
        meta = BiliMeta(
            bvid=bvid,
            aid=aid,
            cid=cid,
            page=selected_page,
            title=title,
            duration=duration or 0,
            thumbnail=thumbnail,
            owner=owner or "",
            webpage_url=webpage_url,
        )
        return info, meta

    # ------------------------------------------------------------------ subtitles
    def get_subtitles(self, url: str, language: str | None = None) -> SubtitlePayload:
        _, meta = self.parse(url)
        data = self._request("/x/player/wbi/v2", {"bvid": meta.bvid, "cid": meta.cid}, signed=True)
        subtitle = (data.get("subtitle") or {}) if isinstance(data, dict) else {}
        items = subtitle.get("subtitles") or []
        if not items:
            if not settings.bilibili_logged_in:
                raise NoSubtitlesError(
                    "这个 B 站视频没有公开 CC 字幕；B 站字幕通常需要登录 Cookie（BILIBILI_SESSDATA）才能读取。"
                )
            raise NoSubtitlesError("这个 B 站视频没有可用 CC 字幕。")

        selected = _select_subtitle_item(items, language)
        if selected is None:
            raise NoSubtitlesError("这个 B 站视频没有可用 CC 字幕。")
        code = str(selected.get("lan") or "")
        subtitle_url = _https(selected.get("subtitle_url"))
        if not subtitle_url:
            raise NoSubtitlesError("B 站返回了字幕语言，但字幕地址为空。")
        try:
            response = requests.get(subtitle_url, headers={**BASE_HEADERS, "Referer": meta.webpage_url}, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise NoSubtitlesError("字幕文件下载失败，请稍后重试。") from exc

        segments = parse_bilibili_subtitle(payload)
        if not segments:
            raise NoSubtitlesError("字幕文件为空，无法生成 AI 总结。")
        transcript, truncated = transcript_from_segments(segments, max_chars=40000)
        name = str(selected.get("lan_doc") or language_name(code))
        is_ai = str(selected.get("lan") or "").startswith("ai-") or "AI" in name
        return SubtitlePayload(
            language=code,
            language_name=name,
            source="哔哩哔哩 AI 字幕" if is_ai else "哔哩哔哩 CC 字幕",
            segments=[SubtitleSegment(**segment.as_dict()) for segment in segments],
            full_text=transcript,
            truncated=truncated,
        )

    # ------------------------------------------------------------------ download
    def _select_streams(self, playurl: dict, option_id: str) -> tuple[dict | None, dict | None, str]:
        dash = playurl.get("dash") or {}
        audio_items = dash.get("audio") or []
        best_audio = max(audio_items, key=lambda item: int(item.get("bandwidth") or 0), default=None)
        if str(option_id or "").strip().lower() == "bili-audio":
            return None, best_audio, "m4a"
        match = OPTION_RE.match(option_id or "")
        if not match:
            videos = dash.get("video") or []
            best = max(videos, key=lambda item: int(item.get("height") or 0), default=None)
            return best, best_audio, "mp4"
        if match.group(1).lower() == "audio":
            return None, best_audio, "m4a"
        qn = int(match.group(1))
        wanted_family = match.group(2).lower()
        candidates = [item for item in dash.get("video") or [] if int(item.get("id") or 0) == qn]
        family_match = [item for item in candidates if _codec_family(str(item.get("codecs") or "")) == wanted_family]
        video = (family_match or candidates or [None])[0]
        if video is None:
            videos = dash.get("video") or []
            video = max(videos, key=lambda item: int(item.get("height") or 0), default=None)
        return video, best_audio, "mp4"

    def _download_stream(
        self,
        entry: dict,
        destination: Path,
        progress: Callable[[float, str], None],
        start_pct: float,
        end_pct: float,
        max_bytes: int,
    ) -> int:
        urls = [entry.get("baseUrl")] + list(entry.get("backupUrl") or [])
        urls = [url for url in urls if url]
        if not urls:
            raise AppError("B 站没有返回可用的下载地址。", code="bilibili_no_url", status_code=502)
        last_error: Exception | None = None
        for url in urls:
            for attempt in range(2):
                try:
                    with requests.get(
                        url,
                        headers={**BASE_HEADERS, "Referer": "https://www.bilibili.com/"},
                        stream=True,
                        timeout=(20, 120),
                    ) as response:
                        if response.status_code not in (200, 206):
                            raise AppError(
                                f"B 站 CDN 返回 {response.status_code}，正在尝试备用线路。",
                                code="bilibili_cdn",
                                status_code=502,
                            )
                        total = int(response.headers.get("Content-Length") or 0)
                        expected = total or int(entry.get("size") or 0)
                        written = 0
                        with destination.open("wb") as handle:
                            for chunk in response.iter_content(chunk_size=256 * 1024):
                                if not chunk:
                                    continue
                                handle.write(chunk)
                                written += len(chunk)
                                if written > max_bytes:
                                    raise AppError("文件超过大小限制。", code="file_too_large", status_code=413)
                                if expected:
                                    ratio = min(1.0, written / expected)
                                    progress(start_pct + (end_pct - start_pct) * ratio, "正在下载")
                                elif written > 0:
                                    progress(start_pct, "正在下载")
                        if written <= 0:
                            raise AppError("B 站 CDN 返回空文件。", code="empty_file", status_code=502)
                        return written
                except AppError as exc:
                    last_error = exc
                    if destination.exists():
                        destination.unlink(missing_ok=True)
                    if exc.code == "file_too_large":
                        raise
                except Exception as exc:
                    last_error = exc
                    if destination.exists():
                        destination.unlink(missing_ok=True)
        raise AppError(f"B 站下载失败：{last_error}", code="bilibili_download", status_code=502)

    def download(
        self,
        url: str,
        option_id: str,
        job_dir: Path,
        progress: Callable[[float, str], None],
        max_bytes: int,
    ) -> tuple[Path, str, str]:
        _, meta = self.parse(url)
        playurl = self._playurl(meta.bvid, meta.aid, meta.cid)
        video, audio, ext = self._select_streams(playurl, option_id)
        audio_only = ext == "m4a"
        if audio_only and not audio:
            raise AppError("该视频没有可用音频流。", code="bilibili_no_audio", status_code=422)
        if not audio_only and not video:
            raise AppError("该视频没有可用视频流。", code="bilibili_no_video", status_code=422)
        if not audio:
            raise AppError("该视频没有可用音频流。", code="bilibili_no_audio", status_code=422)

        base = safe_filename(meta.title, "m4a" if audio_only else "mp4")
        if audio_only:
            target = job_dir / "audio.m4a"
            progress(2, "正在准备音频")
            self._download_stream(audio, target, progress, 2, 98, max_bytes)
            ensure_file(str(target))
            progress(100, "下载完成")
            return target, "m4a", base

        video_path = job_dir / "video.m4s"
        audio_path = job_dir / "audio.m4s"
        progress(1, "正在准备视频")
        self._download_stream(video, video_path, progress, 2, 58, max_bytes)
        progress(59, "正在下载音频")
        self._download_stream(audio, audio_path, progress, 59, 90, max_bytes)
        progress(92, "正在合并音视频")
        output = job_dir / "media.mp4"
        merge_audio_video(str(video_path), str(audio_path), str(output))
        size = ensure_file(str(output))
        if size > max_bytes:
            output.unlink(missing_ok=True)
            raise AppError("文件超过大小限制，已取消。", code="file_too_large", status_code=413)
        for temp in (video_path, audio_path):
            temp.unlink(missing_ok=True)
        progress(100, "下载完成")
        return output, "mp4", base


def _duration_string(duration: int | None) -> str | None:
    if not duration:
        return None
    total = int(duration)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


bili_client = BiliClient()
