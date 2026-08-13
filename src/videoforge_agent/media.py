"""FFprobe metadata and FFmpeg scene analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from videoforge_agent.errors import MediaError
from videoforge_agent.models import MediaInfo, Scene, SelectionConfig
from videoforge_agent.process import CommandRunner

_PTS_TIME = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")


def _fps(value: str) -> float:
    numerator, separator, denominator = value.partition("/")
    if not separator:
        return float(value)
    return float(numerator) / float(denominator)


class MediaAnalyzer:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()

    def probe(self, source: Path) -> MediaInfo:
        result = self.runner.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(source),
            ]
        )
        try:
            payload: dict[str, Any] = json.loads(result.stdout)
            streams = payload["streams"]
            video = next(item for item in streams if item.get("codec_type") == "video")
            duration_raw = video.get("duration") or payload["format"].get("duration")
            duration = float(duration_raw)
            frame_rate = video.get("avg_frame_rate") or video.get("r_frame_rate")
            return MediaInfo(
                path=source,
                duration=duration,
                width=int(video["width"]),
                height=int(video["height"]),
                fps=_fps(str(frame_rate)),
                has_audio=any(item.get("codec_type") == "audio" for item in streams),
            )
        except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MediaError(f"ffprobe returned incomplete metadata for {source}") from exc

    def detect_scenes(self, info: MediaInfo, selection: SelectionConfig) -> list[Scene]:
        """Detect cuts using FFmpeg's normalized inter-frame scene score."""
        result = self.runner.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostdin",
                "-i",
                str(info.path),
                "-an",
                "-filter:v",
                f"select=gt(scene\\,{selection.scene_threshold}),showinfo",
                "-f",
                "null",
                "-",
            ]
        )
        boundaries = [0.0]
        boundaries.extend(float(match) for match in _PTS_TIME.findall(result.stderr))
        boundaries.append(info.duration)
        clean = sorted({round(min(max(point, 0.0), info.duration), 4) for point in boundaries})
        scenes: list[Scene] = []
        for start, end in zip(clean, clean[1:]):
            scenes.extend(self._split_range(info, start, end, selection))
        return [scene for scene in scenes if scene.duration >= selection.min_scene_duration]

    @staticmethod
    def _split_range(
        info: MediaInfo, start: float, end: float, selection: SelectionConfig
    ) -> list[Scene]:
        scenes: list[Scene] = []
        cursor = start
        while end - cursor > selection.max_scene_duration:
            next_end = cursor + selection.max_scene_duration
            scenes.append(
                Scene(source=info.path, start=cursor, end=next_end, has_audio=info.has_audio)
            )
            cursor = next_end
        if end > cursor:
            scenes.append(Scene(source=info.path, start=cursor, end=end, has_audio=info.has_audio))
        return scenes
