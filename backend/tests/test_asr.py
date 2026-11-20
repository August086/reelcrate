from __future__ import annotations

from types import SimpleNamespace

from bilibili import BiliClient, _select_subtitle_item
from config import settings
from schemas import SubtitlePayload, SubtitleSegment
from summarizer import _asr_meta


def test_bilibili_subtitle_prefers_native_chinese_over_ai():
    items = [
        {"lan": "ai-en", "lan_doc": "English (AI)"},
        {"lan": "ai-zh", "lan_doc": "中文 (AI)"},
        {"lan": "zh-Hans", "lan_doc": "简体中文"},
    ]
    assert _select_subtitle_item(items)["lan"] == "zh-Hans"


def test_bilibili_subtitle_prefers_ai_chinese_over_ai_english():
    items = [
        {"lan": "ai-en", "lan_doc": "English (AI)"},
        {"lan": "ai-zh", "lan_doc": "中文 (AI)"},
    ]
    assert _select_subtitle_item(items)["lan"] == "ai-zh"


def test_bilibili_subtitle_honors_requested_language():
    items = [{"lan": "zh-Hans"}, {"lan": "en-US"}]
    assert _select_subtitle_item(items, "en-US")["lan"] == "en-US"


def test_bilibili_audio_option_selects_audio_only():
    client = BiliClient()
    playurl = {
        "dash": {
            "audio": [{"bandwidth": 192000, "baseUrl": "https://example.com/audio.m4s"}],
            "video": [
                {
                    "id": 32,
                    "height": 480,
                    "codecs": "avc1.64001F",
                    "baseUrl": "https://example.com/video.m4s",
                }
            ],
        }
    }
    video, audio, ext = client._select_streams(playurl, "bili-audio")
    assert video is None
    assert audio["baseUrl"] == "https://example.com/audio.m4s"
    assert ext == "m4a"


def test_asr_payload_flag_and_estimate():
    payload = SubtitlePayload(
        language="zh",
        language_name="中文",
        source="本地 Whisper 转写（small）",
        segments=[SubtitleSegment(start=0, end=1, text="测试")],
        full_text="[00:00] 测试",
        asr=True,
    )
    assert payload.asr is True
    assert settings.asr_model in {"small", "medium"}
    assert _asr_meta(SimpleNamespace(duration=600))["asr_estimated_seconds"] > 0


def test_asr_meta_marks_too_long_video():
    info = SimpleNamespace(duration=settings.asr_max_duration_seconds + 1)
    meta = _asr_meta(info)
    assert meta["asr_available"] is False
    assert meta["asr_reason"] == "too_long"
