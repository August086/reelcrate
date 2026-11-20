from __future__ import annotations

import json

import pytest

from downloader import _build_formats
from errors import AppError
from subtitles import (
    Segment,
    parse_bilibili_subtitle,
    parse_json3,
    parse_srt,
    parse_vtt,
    pick_language,
    transcript_from_segments,
)
from summarizer import sse_event
from url_guard import extract_url, safe_filename, validate_public_url


def test_extract_url_from_share_text():
    url = "看这个 https://www.bilibili.com/video/BV1GJ411x7h7/?share_source=copy 谢谢"
    assert extract_url(url) == "https://www.bilibili.com/video/BV1GJ411x7h7/?share_source=copy"


def test_extract_url_adds_scheme():
    assert extract_url("www.bilibili.com/video/BV1GJ411x7h7").startswith("https://")


def test_extract_url_rejects_plain_text():
    with pytest.raises(AppError):
        extract_url("hello world")


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/",
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://[::1]/",
    ],
)
def test_private_addresses_are_blocked(url):
    with pytest.raises(AppError):
        validate_public_url(url)


def test_safe_filename():
    assert safe_filename("a/b:c*?", "mp4") == "a b c.mp4"
    assert safe_filename("", "m4a") == "video.m4a"
    assert safe_filename("标题已带.mp4", "mp4") == "标题已带.mp4"


def test_parse_vtt_with_tags_and_duplicate_cues():
    text = """WEBVTT

NOTE generated
00:00:01.000 --> 00:00:03.000 align:start position:0%
<v Speaker>你好</v>

00:00:03.000 --> 00:00:05.000
你好

00:00:06.500 --> 00:00:08.000
第二句
"""
    segments = parse_vtt(text)
    assert [(s.start, s.end, s.text) for s in segments] == [
        (1.0, 3.0, "你好"),
        (6.5, 8.0, "第二句"),
    ]


def test_parse_srt():
    text = """1
00:00:01,250 --> 00:00:03,500
第一句

2
00:00:04,000 --> 00:00:06,000
第二句
"""
    segments = parse_srt(text)
    assert len(segments) == 2
    assert segments[0].start == 1.25
    assert segments[1].text == "第二句"


def test_parse_bilibili_subtitle():
    payload = {"body": [{"from": 0.5, "to": 2.0, "content": "测试字幕"}]}
    segments = parse_bilibili_subtitle(payload)
    assert segments == [Segment(0.5, 2.0, "测试字幕")]


def test_parse_json3():
    payload = {
        "events": [
            {"tStartMs": 1000, "dDurationMs": 2000, "segs": [{"utf8": "自动"}, {"utf8": "字幕"}]}
        ]
    }
    segments = parse_json3(payload)
    assert len(segments) == 1
    assert segments[0].text == "自动字幕"


def test_pick_language_prefers_chinese():
    assert pick_language(["en", "zh-Hans", "ja"]) == "zh-Hans"
    assert pick_language(["en", "ja"]) == "en"
    assert pick_language(["ja"], "ja") == "ja"


def test_transcript_truncation():
    segments = [Segment(index, index + 1, f"第 {index} 行字幕内容") for index in range(200)]
    text, truncated = transcript_from_segments(segments, max_chars=300)
    assert truncated is True
    assert "中间字幕已省略" in text
    assert len(text) <= 340


def test_build_formats_estimates_size_and_quality():
    info = {
        "duration": 60,
        "formats": [
            {
                "format_id": "137",
                "height": 720,
                "vcodec": "avc1.4d401f",
                "acodec": "none",
                "ext": "mp4",
                "tbr": 2000,
                "url": "https://example.com/v",
            },
            {
                "format_id": "140",
                "vcodec": "none",
                "acodec": "mp4a.40.2",
                "ext": "m4a",
                "tbr": 128,
                "url": "https://example.com/a",
            },
        ],
    }
    options = _build_formats(info, 60)
    video = options[0]
    assert video.label == "720P"
    assert video.quality == "AVC1"
    assert video.needs_merge is True
    assert video.recommended is True
    assert video.filesize == int((2000 + 128) * 60 * 1000 / 8)
    assert options[1].kind == "audio"


def test_build_formats_generic_single_file():
    info = {"title": "demo", "url": "https://example.com/a.mp4", "ext": "mp4"}
    options = _build_formats(info, 10)
    assert len(options) == 1
    assert options[0].id == "yt-video-best"
    assert options[0].needs_merge is False


def test_sse_event_keeps_newlines_inside_json():
    event = sse_event("summary", {"delta": "第一行\n第二行"})
    assert event.startswith("event: summary\ndata: ")
    assert event.endswith("\n\n")
    payload = json.loads(event.split("data: ", 1)[1].strip())
    assert payload["delta"] == "第一行\n第二行"
