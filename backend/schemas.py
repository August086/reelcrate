from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class FormatOption(BaseModel):
    id: str
    label: str = Field(description="短标签，例如 1080P")
    quality: str = Field(description="完整描述，例如 1080P 高清")
    height: int | None = None
    ext: str = "mp4"
    filesize: int | None = None
    kind: Literal["video", "audio"] = "video"
    recommended: bool = False
    needs_merge: bool = False
    note: str | None = None


class SubtitleLanguage(BaseModel):
    code: str
    name: str


class VideoInfo(BaseModel):
    id: str
    title: str
    thumbnail: str | None = None
    duration: int | None = None
    duration_string: str | None = None
    uploader: str | None = None
    platform: str
    platform_key: str
    view_count: int | None = None
    upload_date: str | None = None
    webpage_url: str
    formats: list[FormatOption] = Field(default_factory=list)
    subtitles: list[SubtitleLanguage] = Field(default_factory=list)
    source: Literal["bilibili", "ytdlp"]
    notes: list[str] = Field(default_factory=list)


class ParseRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


class ParseResponse(BaseModel):
    success: Literal[True] = True
    data: VideoInfo


class DirectURLRequest(BaseModel):
    url: str
    option_id: str | None = None


class DirectURLData(BaseModel):
    direct_url: str
    filename: str
    ext: str
    filesize: int | None = None


class DirectURLResponse(BaseModel):
    success: Literal[True] = True
    data: DirectURLData


class DownloadRequest(BaseModel):
    url: str
    option_id: str
    prefer: Literal["proxy", "direct"] = "proxy"


class JobInfo(BaseModel):
    id: str
    status: Literal["queued", "preparing", "downloading", "merging", "ready", "error"]
    mode: Literal["proxy", "direct"] = "proxy"
    progress: float = 0.0
    stage: str = ""
    filename: str | None = None
    filesize: int | None = None
    direct_url: str | None = None
    error: str | None = None
    error_code: str | None = None


class SummarizeRequest(BaseModel):
    url: str
    language: str | None = None
    allow_asr: bool = False


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=20000)


class ChatRequest(BaseModel):
    url: str | None = None
    question: str = Field(min_length=1, max_length=4000)
    subtitle_text: str | None = Field(default=None, max_length=80000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value


class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str


class SubtitlePayload(BaseModel):
    language: str
    language_name: str
    source: str
    segments: list[SubtitleSegment]
    full_text: str
    truncated: bool = False
    asr: bool = False
