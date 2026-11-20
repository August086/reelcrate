from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.app_name = "片匣 PIANXIA"
        self.version = "1.1.0"
        self.deepseek_api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
        self.deepseek_base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1").rstrip("/")
        self.deepseek_model = (os.getenv("DEEPSEEK_MODEL") or "deepseek-chat").strip()
        self.bilibili_sessdata = (os.getenv("BILIBILI_SESSDATA") or "").strip()
        self.bilibili_cookie = (os.getenv("BILIBILI_COOKIE") or "").strip()
        self.ytdlp_cookiefile = (os.getenv("YTDLP_COOKIEFILE") or "").strip()
        self.downloads_dir = Path(os.getenv("DOWNLOADS_DIR", str(BASE_DIR / "downloads"))).resolve()
        self.max_file_size = _int_env("MAX_FILE_SIZE_MB", 2048) * 1024 * 1024
        self.max_concurrent_downloads = max(1, _int_env("MAX_CONCURRENT_DOWNLOADS", 2))
        self.job_ttl_seconds = max(60, _int_env("JOB_TTL_SECONDS", 1800))
        self.info_cache_ttl = max(60, _int_env("INFO_CACHE_TTL", 600))
        self.cors_origins = [
            item.strip()
            for item in (os.getenv("CORS_ORIGINS") or "http://localhost:5173,http://127.0.0.1:5173").split(",")
            if item.strip()
        ]

        # Local Whisper fallback for videos without platform subtitles.
        self.asr_enabled = _bool_env("ASR_ENABLED", True)
        self.asr_auto = _bool_env("ASR_AUTO", False)
        self.asr_model = (os.getenv("ASR_MODEL") or "small").strip().lower()
        if self.asr_model not in {"small", "medium"}:
            self.asr_model = "small"
        default_model_ids = {
            "small": "Systran/faster-whisper-small",
            "medium": "Systran/faster-whisper-medium",
        }
        self.asr_model_id = (os.getenv("ASR_MODEL_ID") or default_model_ids[self.asr_model]).strip()
        self.asr_model_size_mb = 486 if self.asr_model == "small" else 1530
        raw_model_dir = (os.getenv("ASR_MODEL_DIR") or "").strip()
        if raw_model_dir:
            model_dir = Path(raw_model_dir)
            if not model_dir.is_absolute():
                model_dir = ROOT_DIR / model_dir
        else:
            model_dir = BASE_DIR / "models" / f"faster-whisper-{self.asr_model}"
        self.asr_model_dir = model_dir.resolve()
        self.asr_model_auto_download = _bool_env("ASR_MODEL_AUTO_DOWNLOAD", True)
        self.asr_device = (os.getenv("ASR_DEVICE") or "cpu").strip()
        self.asr_compute_type = (os.getenv("ASR_COMPUTE_TYPE") or "int8").strip()
        self.asr_cpu_threads = max(1, _int_env("ASR_CPU_THREADS", min(8, os.cpu_count() or 4)))
        self.asr_language = (os.getenv("ASR_LANGUAGE") or "auto").strip()
        if self.asr_language.lower() in {"", "auto", "none"}:
            self.asr_language = None
        self.asr_max_duration_min = max(1, _int_env("ASR_MAX_DURATION_MIN", 60))
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    @property
    def ai_enabled(self) -> bool:
        key = self.deepseek_api_key
        return bool(key) and key not in {"sk-your-key", "your-key", "changeme"}

    @property
    def bilibili_logged_in(self) -> bool:
        return bool(self.bilibili_sessdata)

    @property
    def asr_ready(self) -> bool:
        return (self.asr_model_dir / "model.bin").exists()

    @property
    def asr_max_duration_seconds(self) -> int:
        return self.asr_max_duration_min * 60


settings = Settings()
