from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from typing import AsyncIterator

from openai import AsyncOpenAI

import asr
from config import settings
from downloader import TTLCache, get_subtitles, parse_video
from errors import AIUnavailableError, AppError, NoSubtitlesError
from schemas import ChatRequest, SubtitlePayload
from url_guard import normalize_and_validate

log = logging.getLogger("reelcrate.ai")

subtitle_cache = TTLCache(3600, 60)
_client: AsyncOpenAI | None = None
_client_key: str | None = None

SUMMARY_SYSTEM = """你是「ReelCrate」的资深视频内容编辑，擅长把长视频读薄。
请只依据用户提供的字幕工作，输出简体中文 Markdown，不要编造字幕中没有的信息。

严格按以下结构输出，使用 ## 二级标题：
## 一句话总结
一句不超过 50 字的判断。
## 内容速览
2-3 句话说明视频讲了什么、怎么展开。
## 核心要点
3-6 条，每条以 "- " 开头；能定位到字幕时间的，在句末附上 [MM:SS]。
## 适合谁看
1-2 条，说明人群和观看收益。
## 值得记住的一句话
引用或凝练一句最有价值的话。

语气专业、克制、有信息密度；不要使用“本视频”“up主说”等空话开头，不要输出代码块。"""

MINDMAP_SYSTEM = """你是知识结构化专家。请把给定的视频总结转换成一张思维导图 Markdown。
只输出 Markdown，不要代码块围栏，不要任何解释。
要求：
- 第一行是 `# 根节点`，根节点不超过 18 字。
- 4-6 个一级分支（`##`），每个分支 2-4 个二级节点（`- `）。
- 最多三层，节点短句化，每条不超过 22 字。
- 保留关键数字、方法、结论；不要照抄整段总结。"""

CHAT_SYSTEM = """你是「ReelCrate」的视频内容助手。你只能依据下方字幕回答用户问题。
规则：
- 用简体中文回答，简洁、具体，必要时引用 [MM:SS] 时间戳。
- 字幕没有提到的内容，直接说明“字幕中没有提到”，不要猜测。
- 不要复述整段字幕；优先给结论和依据。
- 如果用户要求总结，按要点列出，不要写客套话。
"""


def _get_client() -> AsyncOpenAI:
    global _client, _client_key
    if not settings.ai_enabled:
        raise AIUnavailableError()
    if _client is None or _client_key != settings.deepseek_api_key:
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=180.0,
            max_retries=1,
        )
        _client_key = settings.deepseek_api_key
    return _client


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _cache_key(url: str, language: str | None = None) -> str:
    return f"{url}|{language or ''}"


def _asr_meta(info) -> dict:
    state = asr.status()
    duration = info.duration or 0
    too_long = bool(duration and duration > settings.asr_max_duration_seconds)
    available = bool(
        settings.asr_enabled
        and state.get("available")
        and not too_long
    )
    reason = None
    if not settings.asr_enabled:
        reason = "disabled"
    elif not state.get("available"):
        reason = "unavailable"
    elif too_long:
        reason = "too_long"
    elif not state.get("ready") and not settings.asr_model_auto_download:
        reason = "model_missing"
    return {
        "asr_available": available,
        "asr_ready": bool(state.get("ready")),
        "asr_model": state.get("model"),
        "asr_model_size_mb": state.get("model_size_mb"),
        "asr_estimated_seconds": asr.estimate_seconds(duration),
        "asr_max_duration_min": settings.asr_max_duration_min,
        "asr_auto": settings.asr_auto,
        "asr_auto_download": settings.asr_model_auto_download,
        "asr_reason": reason,
    }


async def _asr_events(url: str, info) -> AsyncIterator[tuple[str, object]]:
    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()
    cancel = threading.Event()

    def progress(percent: float, message: str) -> None:
        data = {
            "stage": "asr",
            "progress": round(max(0.0, min(100.0, float(percent))), 1),
            "message": message,
        }
        loop.call_soon_threadsafe(events.put_nowait, ("status", data))

    def worker() -> None:
        try:
            payload = asr.transcribe(url, info, progress, cancel)
        except asr.AsrCancelled:
            loop.call_soon_threadsafe(events.put_nowait, ("cancelled", None))
        except Exception as exc:  # AppError or unexpected
            loop.call_soon_threadsafe(events.put_nowait, ("error", exc))
        else:
            loop.call_soon_threadsafe(events.put_nowait, ("result", payload))
        finally:
            loop.call_soon_threadsafe(events.put_nowait, ("end", None))

    threading.Thread(target=worker, name="reelcrate-asr", daemon=True).start()
    try:
        while True:
            try:
                kind, data = await asyncio.wait_for(events.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ("ping", None)
                continue
            if kind == "status":
                yield ("status", data)
            elif kind == "result":
                yield ("result", data)
                return
            elif kind == "error":
                yield ("error", data)
                return
            elif kind == "cancelled":
                return
            else:
                return
    finally:
        cancel.set()


def _friendly_ai_error(exc: Exception) -> tuple[str, str]:
    status = getattr(exc, "status_code", None)
    text = str(exc)
    if status == 401 or "authentication" in text.lower() or "invalid api key" in text.lower():
        return "ai_auth", "DeepSeek API Key 无效，请检查 backend/.env 中的 DEEPSEEK_API_KEY。"
    if status == 402 or "insufficient" in text.lower() or "balance" in text.lower():
        return "ai_quota", "DeepSeek 账户额度不足，请充值后再试。"
    if status == 429 or "rate limit" in text.lower():
        return "ai_rate_limit", "AI 请求过于频繁，请稍后再试。"
    if status == 400:
        return "ai_bad_request", "字幕内容过长或请求格式异常，请换一个视频重试。"
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "ai_timeout", "AI 服务响应超时，请稍后重试。"
    if "connection" in text.lower():
        return "ai_network", "无法连接 DeepSeek，请检查服务器网络。"
    return "ai_error", "AI 服务暂时不可用，请稍后重试。"


async def _stream_deltas(
    messages: list[dict],
    *,
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    client = _get_client()
    stream = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    try:
        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0].delta, "content", None)
            if delta:
                yield delta
    finally:
        close = getattr(stream, "close", None)
        if close:
            try:
                await close()
            except Exception:
                pass


def _context_block(title: str, platform: str, duration: str | None, payload: SubtitlePayload) -> str:
    truncated_note = "\n注意：字幕过长，已做首尾截取。" if payload.truncated else ""
    return (
        f"视频标题：{title}\n"
        f"平台：{platform}\n"
        f"时长：{duration or '未知'}\n"
        f"字幕语言：{payload.language_name}\n"
        f"字幕来源：{payload.source}{truncated_note}\n\n"
        f"字幕：\n{payload.full_text}"
    )


def _strip_fences(markdown: str) -> str:
    text = (markdown or "").strip()
    text = re.sub(r"^```(?:markdown|md)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def summarize_stream(
    url: str,
    language: str | None = None,
    allow_asr: bool = False,
) -> AsyncIterator[str]:
    yield sse_event("status", {"stage": "subtitles", "message": "正在提取字幕…"})
    try:
        normalized = await asyncio.to_thread(normalize_and_validate, url)
        info = await asyncio.to_thread(parse_video, normalized)
        cache_key = _cache_key(normalized, language)
        payload = subtitle_cache.get(cache_key)
        if payload is None:
            try:
                payload = await asyncio.to_thread(get_subtitles, normalized, language)
            except NoSubtitlesError as exc:
                meta = _asr_meta(info)
                permitted = bool(
                    settings.asr_enabled
                    and meta.get("asr_available")
                    and (allow_asr or settings.asr_auto)
                )
                if not permitted:
                    message = exc.message
                    if meta.get("asr_available"):
                        message = f"{message} 可以让本地 Whisper 听一遍。"
                    elif meta.get("asr_reason") == "too_long":
                        message = f"{message} 视频超过 {settings.asr_max_duration_min} 分钟，暂不做本地转写。"
                    yield sse_event(
                        "error",
                        {"code": exc.code, "message": message, **meta},
                    )
                    yield sse_event("done", {})
                    return

                yield sse_event(
                    "status",
                    {"stage": "asr", "progress": 0, "message": "平台没有字幕，准备本地听写…"},
                )
                asr_error: Exception | None = None
                async for kind, data in _asr_events(normalized, info):
                    if kind == "status":
                        yield sse_event("status", data)
                    elif kind == "ping":
                        yield ": ping\n\n"
                    elif kind == "result":
                        payload = data
                    elif kind == "error":
                        asr_error = data
                        break
                if asr_error is not None:
                    raise asr_error
                if payload is None:
                    raise AppError(
                        "本地听写未完成，请重试。",
                        code="asr_empty",
                        status_code=502,
                    )
            subtitle_cache.set(cache_key, payload)

        yield sse_event(
            "subtitle",
            {
                **payload.model_dump(),
                "title": info.title,
                "platform": info.platform,
                "duration_string": info.duration_string,
            },
        )
        if not settings.ai_enabled:
            yield sse_event(
                "error",
                {
                    "code": "ai_not_configured",
                    "message": "字幕已提取，但 AI 服务未配置。请在 backend/.env 设置 DEEPSEEK_API_KEY 后重启后端。",
                },
            )
            yield sse_event("done", {})
            return

        yield sse_event("status", {"stage": "summary", "message": "正在生成总结…"})
        messages = [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {
                "role": "user",
                "content": _context_block(info.title, info.platform, info.duration_string, payload)
                + "\n\n请按固定结构输出总结。",
            },
        ]
        summary_parts: list[str] = []
        async for delta in _stream_deltas(
            messages,
            temperature=0.35,
            max_tokens=2200,
        ):
            summary_parts.append(delta)
            yield sse_event("summary", {"delta": delta})

        summary_text = "".join(summary_parts).strip()
        if not summary_text:
            raise AppError("AI 返回了空总结，请重试。", code="ai_empty", status_code=502)

        yield sse_event("status", {"stage": "mindmap", "message": "正在生成思维导图…"})
        client = _get_client()
        mindmap_response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": MINDMAP_SYSTEM},
                {
                    "role": "user",
                    "content": f"视频标题：{info.title}\n\n视频总结：\n{summary_text}\n\n请生成思维导图。",
                },
            ],
            temperature=0.3,
            max_tokens=1400,
            stream=False,
        )
        mindmap = _strip_fences(mindmap_response.choices[0].message.content or "")
        if not mindmap.startswith("#"):
            mindmap = f"# {info.title}\n\n{mindmap}"
        yield sse_event("mindmap", {"markdown": mindmap})
        yield sse_event("done", {"model": settings.deepseek_model})
    except NoSubtitlesError as exc:
        yield sse_event("error", {"code": exc.code, "message": exc.message})
        yield sse_event("done", {})
    except AIUnavailableError as exc:
        yield sse_event("error", {"code": exc.code, "message": exc.message})
        yield sse_event("done", {})
    except AppError as exc:
        yield sse_event("error", {"code": exc.code, "message": exc.message})
        yield sse_event("done", {})
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log.exception("summarize failed")
        code, message = _friendly_ai_error(exc)
        yield sse_event("error", {"code": code, "message": message})
        yield sse_event("done", {})


async def chat_stream(request: ChatRequest) -> AsyncIterator[str]:
    try:
        subtitle_text = (request.subtitle_text or "").strip()
        title = "当前视频"
        platform = ""
        if request.url:
            info = await asyncio.to_thread(parse_video, request.url)
            title = info.title
            platform = info.platform
            if not subtitle_text:
                payload = await asyncio.to_thread(get_subtitles, request.url, None)
                subtitle_text = payload.full_text
        if not subtitle_text:
            raise AppError("还没有可用字幕，请先解析视频。", code="no_subtitle_context", status_code=422)
        if not settings.ai_enabled:
            raise AIUnavailableError()

        subtitle_text = subtitle_text[:60000]
        system = (
            CHAT_SYSTEM
            + f"\n\n视频标题：{title}\n平台：{platform or '未知'}\n\n字幕：\n"
            + subtitle_text
        )
        messages: list[dict] = [{"role": "system", "content": system}]
        for turn in request.history[-8:]:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": request.question})
        async for delta in _stream_deltas(messages, temperature=0.5, max_tokens=1600):
            yield sse_event("answer", {"delta": delta})
        yield sse_event("done", {})
    except asyncio.CancelledError:
        raise
    except (AppError, NoSubtitlesError, AIUnavailableError) as exc:
        yield sse_event("error", {"code": exc.code, "message": exc.message})
        yield sse_event("done", {})
    except Exception as exc:
        log.exception("chat failed")
        code, message = _friendly_ai_error(exc)
        yield sse_event("error", {"code": code, "message": message})
        yield sse_event("done", {})
