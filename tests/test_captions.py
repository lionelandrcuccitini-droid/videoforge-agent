import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from videoforge_agent.captions import WhisperTranscriber, _timestamp, write_srt
from videoforge_agent.errors import DependencyError
from videoforge_agent.models import CaptionConfig, CaptionSegment


def test_timestamp_handles_hours_and_rounding() -> None:
    assert _timestamp(3661.234) == "01:01:01,234"


def test_write_srt(tmp_path: Path) -> None:
    output = write_srt([CaptionSegment(start=0, end=1.5, text=" 你好 ")], tmp_path / "captions.srt")
    assert output.read_text(encoding="utf-8") == "1\n00:00:00,000 --> 00:00:01,500\n你好\n"


def test_whisper_transcriber_converts_nonempty_segments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("faster_whisper")

    class FakeWhisperModel:
        def __init__(self, model: str, *, device: str, compute_type: str) -> None:
            del model, device, compute_type

        def transcribe(self, video: str, **kwargs: object) -> tuple[list[object], object]:
            del video, kwargs
            return [
                SimpleNamespace(start=0, end=1, text=" hello "),
                SimpleNamespace(start=1, end=2, text=" "),
            ], None

    module.WhisperModel = FakeWhisperModel  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "faster_whisper", module)

    segments = WhisperTranscriber().transcribe(Path("video.mp4"), CaptionConfig(enabled=True))

    assert [segment.text for segment in segments] == [" hello "]


def test_whisper_transcriber_explains_missing_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    with pytest.raises(DependencyError, match=r"videoforge-agent\[transcribe\]"):
        WhisperTranscriber().transcribe(Path("video.mp4"), CaptionConfig(enabled=True))
