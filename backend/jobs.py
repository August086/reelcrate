from __future__ import annotations

import logging
import secrets
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from config import settings
from downloader import download_video, get_direct_url
from errors import AppError
from schemas import JobInfo

log = logging.getLogger("reelcrate.jobs")


@dataclass
class Job:
    id: str
    url: str
    option_id: str
    prefer: str
    status: str = "queued"
    mode: str = "proxy"
    progress: float = 0.0
    stage: str = "排队中"
    filename: str | None = None
    filesize: int | None = None
    direct_url: str | None = None
    error: str | None = None
    error_code: str | None = None
    path: Path | None = None
    dir: Path | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_info(self) -> JobInfo:
        return JobInfo(
            id=self.id,
            status=self.status,  # type: ignore[arg-type]
            mode=self.mode,  # type: ignore[arg-type]
            progress=round(max(0.0, min(100.0, self.progress)), 1),
            stage=self.stage,
            filename=self.filename,
            filesize=self.filesize,
            direct_url=self.direct_url,
            error=self.error,
            error_code=self.error_code,
        )


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=settings.max_concurrent_downloads,
            thread_name_prefix="reelcrate-dl",
        )
        self._stop = threading.Event()
        self._cleaner = threading.Thread(target=self._cleanup_loop, name="reelcrate-janitor", daemon=True)
        self._cleaner.start()
        self._cleanup_orphans()

    def create(self, url: str, option_id: str, prefer: str = "proxy") -> Job:
        job_id = secrets.token_urlsafe(12)
        job_dir = settings.downloads_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        job = Job(
            id=job_id,
            url=url,
            option_id=option_id,
            prefer=prefer,
            dir=job_dir,
        )
        with self._lock:
            self._jobs[job_id] = job
        self._executor.submit(self._run, job)
        return job

    def _update(self, job: Job, **fields) -> None:
        with self._lock:
            for key, value in fields.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def _progress(self, job: Job, percent: float, stage: str) -> None:
        with self._lock:
            if job.status == "error":
                return
            job.progress = max(job.progress, min(99.0, float(percent)))
            job.stage = stage
            job.updated_at = time.time()

    def _run(self, job: Job) -> None:
        try:
            self._update(job, status="preparing", stage="正在准备下载", progress=1)
            if job.prefer == "direct":
                direct = get_direct_url(job.url, job.option_id)
                self._update(
                    job,
                    status="ready",
                    mode="direct",
                    progress=100,
                    stage="直链已就绪",
                    direct_url=str(direct.direct_url),
                    filename=direct.filename,
                    filesize=direct.filesize,
                )
                return
            self._update(job, mode="proxy", status="downloading", stage="正在解析下载地址", progress=2)
            path, ext, filename = download_video(
                job.url,
                job.option_id,
                job.dir or settings.downloads_dir,
                lambda percent, stage: self._progress(job, percent, stage),
                settings.max_file_size,
            )
            size = path.stat().st_size
            self._update(
                job,
                status="ready",
                progress=100,
                stage="下载完成",
                filename=filename,
                filesize=size,
                path=path,
            )
        except AppError as exc:
            log.warning("job %s failed: %s", job.id, exc.message)
            self._update(job, status="error", error=exc.message, error_code=exc.code, stage="下载失败")
            self._remove_dir(job)
        except Exception:
            log.exception("job %s crashed", job.id)
            self._update(job, status="error", error="下载服务异常，请稍后重试。", error_code="internal", stage="下载失败")
            self._remove_dir(job)

    def _remove_dir(self, job: Job) -> None:
        if job.dir and job.dir.exists():
            shutil.rmtree(job.dir, ignore_errors=True)

    def get(self, job_id: str) -> JobInfo:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise AppError("下载任务不存在或已过期。", code="job_not_found", status_code=404)
            return job.to_info()

    def file(self, job_id: str) -> tuple[Path, str]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise AppError("下载任务不存在或已过期。", code="job_not_found", status_code=404)
            if job.status != "ready" or job.mode != "proxy":
                raise AppError("文件还没有准备好。", code="job_not_ready", status_code=409)
            if not job.path or not job.path.exists():
                raise AppError("文件已被清理，请重新下载。", code="file_missing", status_code=404)
            return job.path, job.filename or job.path.name

    def _cleanup_orphans(self) -> None:
        cutoff = time.time() - settings.job_ttl_seconds
        for child in settings.downloads_dir.iterdir() if settings.downloads_dir.exists() else []:
            if not child.is_dir():
                continue
            try:
                if child.stat().st_mtime < cutoff:
                    shutil.rmtree(child, ignore_errors=True)
            except OSError:
                continue

    def _cleanup_loop(self) -> None:
        while not self._stop.wait(300):
            cutoff = time.time() - settings.job_ttl_seconds
            expired: list[Job] = []
            with self._lock:
                for job_id, job in list(self._jobs.items()):
                    if job.updated_at < cutoff and job.status in {"ready", "error"}:
                        expired.append(job)
                        self._jobs.pop(job_id, None)
            for job in expired:
                self._remove_dir(job)

    def shutdown(self) -> None:
        self._stop.set()
        self._executor.shutdown(wait=False, cancel_futures=True)


job_manager = JobManager()
