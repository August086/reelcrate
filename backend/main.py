from __future__ import annotations

import asyncio
import logging
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import asr
from config import ROOT_DIR, settings
from downloader import parse_video
from errors import AppError
from jobs import job_manager
from schemas import (
    ChatRequest,
    DirectURLRequest,
    DownloadRequest,
    ParseRequest,
    ParseResponse,
    SummarizeRequest,
)
from summarizer import chat_stream, summarize_stream
from url_guard import normalize_and_validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("reelcrate")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("%s %s ready; ai=%s; bilibili_login=%s", settings.app_name, settings.version, settings.ai_enabled, settings.bilibili_logged_in)
    yield
    job_manager.shutdown()


app = FastAPI(
    title="ReelCrate API",
    version=settings.version,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    location = ".".join(str(part) for part in first.get("loc", []) if part not in {"body", "query", "path"})
    message = first.get("msg") or "请求参数不正确。"
    if location:
        message = f"{location}：{message}"
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": message, "code": "validation_error"},
    )


@app.get("/api/health")
async def health() -> dict:
    return {"success": True, "data": {"status": "ok", "version": settings.version}}


@app.get("/api/config")
async def config() -> dict:
    return {
        "success": True,
        "data": {
            "app_name": settings.app_name,
            "version": settings.version,
            "ai_enabled": settings.ai_enabled,
            "ai_model": settings.deepseek_model if settings.ai_enabled else None,
            "bilibili_logged_in": settings.bilibili_logged_in,
            "max_file_size_mb": settings.max_file_size // (1024 * 1024),
            "platform_count": "1800+",
            "asr": asr.status(),
        },
    }


@app.post("/api/parse", response_model=ParseResponse)
async def parse_video_endpoint(payload: ParseRequest) -> ParseResponse:
    info = await asyncio.to_thread(parse_video, payload.url)
    return ParseResponse(data=info)


@app.post("/api/downloads")
async def create_download(payload: DownloadRequest) -> dict:
    url = await asyncio.to_thread(normalize_and_validate, payload.url)
    if not payload.option_id:
        raise AppError("请选择下载清晰度。", code="missing_option")
    job = job_manager.create(url, payload.option_id, payload.prefer)
    return {"success": True, "data": {"job_id": job.id, "mode": "proxy", "status": job.status}}


@app.get("/api/downloads/{job_id}")
async def download_status(job_id: str) -> dict:
    job = job_manager.get(job_id)
    return {"success": True, "data": job.model_dump()}


@app.get("/api/downloads/{job_id}/file")
async def download_file(job_id: str) -> FileResponse:
    path, filename = job_manager.file(job_id)
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/direct-url")
async def direct_url(payload: DirectURLRequest) -> dict:
    from downloader import get_direct_url

    data = await asyncio.to_thread(get_direct_url, payload.url, payload.option_id)
    return {"success": True, "data": data.model_dump()}


@app.post("/api/summarize")
async def summarize(payload: SummarizeRequest) -> StreamingResponse:
    return StreamingResponse(
        summarize_stream(payload.url, payload.language, payload.allow_asr),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        chat_stream(payload),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


frontend_dist = ROOT_DIR / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
