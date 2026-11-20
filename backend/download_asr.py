"""Pre-download the local Whisper model.

Usage (from the repository root):
    .\\.venv\\Scripts\\python.exe backend\\download_asr.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings  # noqa: E402
from asr import _ensure_model  # noqa: E402


def main() -> None:
    print(f"Preparing ASR model: {settings.asr_model_id}")
    path = _ensure_model(lambda percent, message: print(f"{percent:5.1f}% {message}"))
    print(f"Model ready: {path}")


if __name__ == "__main__":
    main()
