import json
from pathlib import Path

import pytest

from videoforge_agent.errors import MediaError
from videoforge_agent.media import MediaAnalyzer
from videoforge_agent.models import MediaInfo, SelectionConfig
from videoforge_agent.process import CommandResult


class FakeRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def run(self, args: list[str], *, cwd: Path | None = None) -> CommandResult:
        del cwd
        self.calls.append(args)
        return self.result


def test_probe_parses_video_and_audio() -> None:
    payload = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "30000/1001",
                "duration": "12.5",
            },
            {"codec_type": "audio"},
        ],
        "format": {"duration": "12.5"},
    }
    runner = FakeRunner(CommandResult(json.dumps(payload), ""))
    analyzer = MediaAnalyzer(runner)  # type: ignore[arg-type]

    info = analyzer.probe(Path("clip.mp4"))

    assert info.duration == 12.5
    assert info.has_audio is True
    assert info.fps == pytest.approx(29.97, rel=1e-3)


def test_probe_rejects_incomplete_metadata() -> None:
    analyzer = MediaAnalyzer(FakeRunner(CommandResult("{}", "")))  # type: ignore[arg-type]
    with pytest.raises(MediaError, match="incomplete metadata"):
        analyzer.probe(Path("clip.mp4"))


def test_scene_detection_splits_long_ranges() -> None:
    stderr = "[showinfo] n:1 pts:1 pts_time:4.0\n[showinfo] n:2 pts:2 pts_time:13.0"
    analyzer = MediaAnalyzer(FakeRunner(CommandResult("", stderr)))  # type: ignore[arg-type]
    info = MediaInfo(
        path=Path("clip.mp4"), duration=20, width=100, height=100, fps=30, has_audio=False
    )

    scenes = analyzer.detect_scenes(
        info, SelectionConfig(min_scene_duration=1, max_scene_duration=5, scene_threshold=0.3)
    )

    assert [(item.start, item.end) for item in scenes] == [
        (0, 4),
        (4, 9),
        (9, 13),
        (13, 18),
        (18, 20),
    ]
    assert all(not item.has_audio for item in scenes)
