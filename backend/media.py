from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache

from errors import AppError


@lru_cache(maxsize=1)
def ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg

        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    return shutil.which("ffmpeg") or ""


def _run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess:
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=flags,
    )


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise AppError("服务器未安装 ffmpeg，无法合并音视频。", code="ffmpeg_missing", status_code=500)
    base = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", video_path, "-i", audio_path]
    copy_cmd = base + ["-c", "copy", "-movflags", "+faststart", output_path]
    result = _run(copy_cmd)
    if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return

    # HE-AAC / unusual DASH streams can reject -c copy in old builds; re-encode audio only.
    fallback_cmd = base + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path]
    result = _run(fallback_cmd)
    if result.returncode != 0 or not os.path.exists(output_path):
        detail = (result.stderr or "").strip().splitlines()[-1:] or ["未知错误"]
        raise AppError(f"音视频合并失败：{detail[0]}", code="merge_failed", status_code=500)


def ensure_file(path: str, min_bytes: int = 1) -> int:
    if not os.path.exists(path):
        raise AppError("下载文件不存在，请重试。", code="file_missing", status_code=500)
    size = os.path.getsize(path)
    if size < min_bytes:
        raise AppError("下载结果为空，请稍后重试。", code="empty_file", status_code=500)
    return size
