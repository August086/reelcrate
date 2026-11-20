from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urlsplit, urlunsplit

from errors import AppError

URL_RE = re.compile(r"(?:https?://)?(?:[\w-]+\.)+[a-zA-Z]{2,}(?::\d{2,5})?(?:/[^\s<>\"']*)?")
TRAILING = ".,;:!?，。；：！？、）)]】》」』"


def extract_url(text: str) -> str:
    """Accept pasted share text and return the first URL-like token."""
    if not text or not text.strip():
        raise AppError("请输入视频链接。", code="invalid_url")
    cleaned = html.unescape(text).strip()
    match = URL_RE.search(cleaned)
    if not match:
        raise AppError("没有识别到有效链接，请检查后重试。", code="invalid_url")
    candidate = match.group(0).rstrip(TRAILING)
    if not re.match(r"^https?://", candidate, re.I):
        candidate = "https://" + candidate
    return candidate


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    return not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_loopback or ip.is_link_local


def validate_public_url(url: str) -> str:
    """Validate scheme + destination before handing the URL to yt-dlp."""
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise AppError("链接格式不正确。", code="invalid_url") from exc

    if parts.scheme not in {"http", "https"}:
        raise AppError("只支持 http/https 链接。", code="invalid_url")
    host = (parts.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise AppError("链接缺少域名。", code="invalid_url")
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".lan", ".home")):
        raise AppError("不允许访问内网地址。", code="blocked_url", status_code=403)
    if len(url) > 2048:
        raise AppError("链接过长，请使用原始视频链接。", code="invalid_url")

    try:
        infos = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AppError("域名解析失败，请检查网络或链接。", code="invalid_url") from exc

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if _is_blocked_ip(ip):
            raise AppError("该链接指向受限地址，已拦截。", code="blocked_url", status_code=403)

    # Drop fragments; keep query (needed by many platforms).
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def normalize_and_validate(text_or_url: str) -> str:
    return validate_public_url(extract_url(text_or_url))


def safe_filename(name: str, ext: str = "mp4", fallback: str = "video") -> str:
    name = html.unescape(name or "").strip()
    name = re.sub(r"[\x00-\x1f\x7f/\\:*?\"<>|]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = fallback
    if len(name) > 96:
        name = name[:96].rstrip(" .")
    ext = (ext or "mp4").lstrip(".").lower()
    if ext and not name.lower().endswith("." + ext):
        name = f"{name}.{ext}"
    return name
