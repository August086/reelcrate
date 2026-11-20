from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, *, code: str = "bad_request", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NoSubtitlesError(AppError):
    def __init__(self, message: str = "没有找到可用字幕，无法生成 AI 总结。") -> None:
        super().__init__(message, code="no_subtitles", status_code=422)


class AIUnavailableError(AppError):
    def __init__(self, message: str = "AI 服务未配置，请设置 DEEPSEEK_API_KEY。") -> None:
        super().__init__(message, code="ai_not_configured", status_code=503)


class UnsupportedURLError(AppError):
    def __init__(self, message: str = "该链接暂不支持，请换一个视频链接。") -> None:
        super().__init__(message, code="unsupported_url", status_code=422)
