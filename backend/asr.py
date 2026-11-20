from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Callable

import numpy as np

from bilibili import is_bilibili_url
from config import settings
from downloader import download_video
from errors import AppError
from media import ffmpeg_path
from schemas import SubtitlePayload, SubtitleSegment
from subtitles import Segment, language_name, transcript_from_segments

log = logging.getLogger("pianxia.asr")

Progress = Callable[[float, str], None]


class AsrError(AppError):
    def __init__(self, message: str, *, code: str = "asr_failed", status_code: int = 502) -> None:
        super().__init__(message, code=code, status_code=status_code)


class AsrCancelled(Exception):
    """Raised when the SSE client disconnects during transcription."""


_model = None
_model_lock = threading.Lock()
_model_prepare_lock = threading.Lock()
_transcribe_lock = threading.Lock()


def is_available() -> bool:
    try:
        import faster_whisper  # noqa: F401

        return True
    except Exception:
        return False


def status() -> dict:
    return {
        "enabled": settings.asr_enabled,
        "available": is_available(),
        "ready": settings.asr_ready,
        "model": settings.asr_model,
        "model_size_mb": settings.asr_model_size_mb,
        "max_duration_min": settings.asr_max_duration_min,
        "auto": settings.asr_auto,
        "auto_download": settings.asr_model_auto_download,
    }


def estimate_seconds(duration: int | None) -> int:
    if not duration:
        return 120
    model_overhead = 0 if settings.asr_ready else 40
    # Measured on this machine: small/int8 on 8 CPU threads ≈ 0.162x realtime.
    return int(12 + model_overhead + max(10, duration * 0.20))


def _ensure_model(progress: Progress | None = None) -> Path:
    path = settings.asr_model_dir
    if (path / "model.bin").exists():
        return path
    if not settings.asr_enabled:
        raise AsrError("本地语音转写未启用。", code="asr_disabled", status_code=503)
    if not settings.asr_model_auto_download:
        raise AsrError(
            "语音模型未下载。请运行 backend/download_asr.py，或设置 ASR_MODEL_AUTO_DOWNLOAD=true。",
            code="asr_model_missing",
            status_code=503,
        )

    with _model_prepare_lock:
        if (path / "model.bin").exists():
            return path
        path.mkdir(parents=True, exist_ok=True)
        if progress:
            progress(18, f"首次使用，正在下载语音模型（约 {settings.asr_model_size_mb}MB）…")
        try:
            from modelscope import snapshot_download

            snapshot_download(settings.asr_model_id, local_dir=str(path))
        except Exception as exc:
            log.exception("ASR model download failed")
            raise AsrError(
                "语音模型下载失败，请检查网络后重试，或运行 backend/download_asr.py。",
                code="asr_model_download_failed",
                status_code=502,
            ) from exc
        if not (path / "model.bin").exists():
            raise AsrError(
                "语音模型下载不完整，请删除模型目录后重试。",
                code="asr_model_incomplete",
                status_code=502,
            )
    return path


def _get_model(progress: Progress | None = None):
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        model_path = _ensure_model(progress)
        if progress:
            progress(27, "正在加载语音模型…")
        try:
            from faster_whisper import WhisperModel

            _model = WhisperModel(
                str(model_path),
                device=settings.asr_device,
                compute_type=settings.asr_compute_type,
                cpu_threads=settings.asr_cpu_threads,
            )
        except Exception as exc:
            log.exception("ASR model load failed")
            raise AsrError(
                "语音模型加载失败，请检查 ASR_MODEL / ASR_COMPUTE_TYPE 配置。",
                code="asr_model_load_failed",
                status_code=502,
            ) from exc
    return _model


def _download_audio(url: str, work_dir: Path, progress: Progress, cancel: threading.Event, max_bytes: int) -> Path:
    option_id = "bili-audio" if is_bilibili_url(url) else "yt-audio"

    def on_download(percent: float, message: str) -> None:
        if cancel.is_set():
            raise AsrCancelled()
        mapped = 2 + min(14.0, float(percent) / 100 * 14)
        progress(mapped, message)

    if progress:
        progress(2, "正在准备音频…")
    path, _ext, _name = download_video(url, option_id, work_dir, on_download, max_bytes)
    if cancel.is_set():
        raise AsrCancelled()
    return path


def _to_pcm(audio_path: Path, pcm_path: Path, progress: Progress) -> None:
    ffmpeg = ffmpeg_path()
    if not ffmpeg:
        raise AsrError("服务器缺少 ffmpeg，无法准备转写音频。", code="ffmpeg_missing", status_code=500)
    if progress:
        progress(16, "正在转换为 16k 单声道音频…")
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(audio_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "s16le",
        str(pcm_path),
    ]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            creationflags=flags,
        )
    except subprocess.TimeoutExpired as exc:
        raise AsrError("音频转换超时，请尝试更短的视频。", code="asr_audio_timeout", status_code=504) from exc
    if result.returncode != 0 or not pcm_path.exists() or pcm_path.stat().st_size == 0:
        detail = (result.stderr or "").strip().splitlines()[-1:] or ["未知错误"]
        raise AsrError(f"音频转换失败：{detail[0]}", code="asr_audio_failed", status_code=502)


def _read_pcm(path: Path) -> np.ndarray:
    data = np.fromfile(path, dtype=np.int16)
    if data.size == 0:
        raise AsrError("音频为空，无法转写。", code="asr_empty_audio", status_code=422)
    return data.astype(np.float32) / 32768.0


def transcribe(url: str, info, progress: Progress, cancel: threading.Event) -> SubtitlePayload:
    """Download audio and transcribe it with a local faster-whisper model.

    This function is intentionally synchronous; callers run it in a worker thread.
    """
    if not settings.asr_enabled:
        raise AsrError("本地语音转写未启用。", code="asr_disabled", status_code=503)
    duration = info.duration or 0
    if duration and duration > settings.asr_max_duration_seconds:
        raise AsrError(
            f"视频时长超过 {settings.asr_max_duration_min} 分钟，暂不做本地转写。",
            code="asr_too_long",
            status_code=422,
        )

    work_dir = settings.downloads_dir / f"asr-{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        audio_path = _download_audio(url, work_dir, progress, cancel, settings.max_file_size)
        pcm_path = work_dir / "audio.pcm"
        _to_pcm(audio_path, pcm_path, progress)
        if cancel.is_set():
            raise AsrCancelled()
        audio = _read_pcm(pcm_path)
        audio_duration = len(audio) / 16000.0
        if audio_duration > settings.asr_max_duration_seconds:
            raise AsrError(
                f"音频超过 {settings.asr_max_duration_min} 分钟，暂不做本地转写。",
                code="asr_too_long",
                status_code=422,
            )

        model = _get_model(progress)
        if cancel.is_set():
            raise AsrCancelled()
        if progress:
            progress(30, "正在本地听写…")
        segments: list[Segment] = []
        detected_language = None
        with _transcribe_lock:
            try:
                segment_iter, transcription_info = model.transcribe(
                    audio,
                    language=settings.asr_language,
                    beam_size=5,
                    vad_filter=True,
                    condition_on_previous_text=False,
                    initial_prompt=f"{info.title}。",
                )
            except Exception as exc:
                log.exception("ASR transcribe failed")
                raise AsrError("语音转写失败，请稍后重试。", code="asr_failed", status_code=502) from exc
            detected_language = getattr(transcription_info, "language", None)
            last_percent = 30.0
            try:
                for segment in segment_iter:
                    if cancel.is_set():
                        raise AsrCancelled()
                    text = str(getattr(segment, "text", "") or "").strip()
                    if text:
                        segments.append(Segment(float(segment.start), float(segment.end), text))
                    if progress and duration:
                        percent = 30 + min(66.0, max(0.0, float(segment.end) / duration * 66.0))
                        if percent - last_percent >= 2:
                            progress(percent, f"正在听写 {int(segment.end // 60):02d}:{int(segment.end % 60):02d} / {info.duration_string or ''}")
                            last_percent = percent
            except AsrCancelled:
                raise
            except Exception as exc:
                log.exception("ASR segment iteration failed")
                raise AsrError("语音转写中断，请稍后重试。", code="asr_failed", status_code=502) from exc

        if not segments:
            raise AsrError("没有识别到语音内容，无法生成字幕。", code="asr_empty", status_code=422)
        transcript, truncated = transcript_from_segments(segments, max_chars=40000)
        language = detected_language or settings.asr_language or "unknown"
        if progress:
            progress(100, "本地听写完成")
        return SubtitlePayload(
            language=str(language),
            language_name=language_name(str(language)),
            source=f"本地 Whisper 转写（{settings.asr_model}）",
            segments=[SubtitleSegment(**segment.as_dict()) for segment in segments],
            full_text=transcript,
            truncated=truncated,
            asr=True,
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
