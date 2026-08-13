from pathlib import Path

from videoforge_agent.captions import _timestamp, write_srt
from videoforge_agent.models import CaptionSegment


def test_timestamp_handles_hours_and_rounding() -> None:
    assert _timestamp(3661.234) == "01:01:01,234"


def test_write_srt(tmp_path: Path) -> None:
    output = write_srt(
        [CaptionSegment(start=0, end=1.5, text=" 你好 ")], tmp_path / "captions.srt"
    )
    assert output.read_text(encoding="utf-8") == "1\n00:00:00,000 --> 00:00:01,500\n你好\n"

