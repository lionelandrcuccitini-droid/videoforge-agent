"""Optional Whisper transcription and standard SRT output."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from videoforge_agent.errors import DependencyError
from videoforge_agent.models import CaptionConfig, CaptionSegment


def _timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: Iterable[CaptionSegment], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        f"{index}\n{_timestamp(segment.start)} --> {_timestamp(segment.end)}\n{segment.text.strip()}"
        for index, segment in enumerate(segments, start=1)
    ]
    output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return output


class WhisperTranscriber:
    def transcribe(self, video: Path, config: CaptionConfig) -> list[CaptionSegment]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise DependencyError(
                "captions require: python -m pip install 'videoforge-agent[transcribe]'"
            ) from exc
        model: Any = WhisperModel(config.model, device="auto", compute_type="auto")
        raw_segments, _ = model.transcribe(
            str(video), language=config.language, vad_filter=True, beam_size=5
        )
        return [
            CaptionSegment(start=float(item.start), end=float(item.end), text=str(item.text))
            for item in raw_segments
            if str(item.text).strip()
        ]

