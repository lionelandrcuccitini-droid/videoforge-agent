"""Compile a reviewed edit plan into one FFmpeg render."""

from __future__ import annotations

import os
from pathlib import Path

from videoforge_agent.models import EditPlan, OutputConfig
from videoforge_agent.process import CommandRunner


class FFmpegRenderer:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()

    def render(self, plan: EditPlan, output: OutputConfig) -> Path:
        output.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.path.with_name(f".{output.path.stem}.rendering{output.path.suffix}")
        args = ["ffmpeg", "-hide_banner", "-nostdin", "-y"]
        for clip in plan.clips:
            args.extend(["-i", str(clip.source)])

        filters: list[str] = []
        concat_inputs: list[str] = []
        for index, clip in enumerate(plan.clips):
            filters.append(
                f"[{index}:v]trim=start={clip.start:.4f}:end={clip.end:.4f},"
                "setpts=PTS-STARTPTS,"
                f"scale={output.width}:{output.height}:force_original_aspect_ratio=increase,"
                f"crop={output.width}:{output.height},fps={output.fps},setsar=1[v{index}]"
            )
            if clip.has_audio:
                filters.append(
                    f"[{index}:a]atrim=start={clip.start:.4f}:end={clip.end:.4f},"
                    f"asetpts=PTS-STARTPTS,aresample=48000[a{index}]"
                )
            else:
                filters.append(
                    "anullsrc=r=48000:cl=stereo,"
                    f"atrim=duration={clip.duration:.4f},asetpts=PTS-STARTPTS[a{index}]"
                )
            concat_inputs.append(f"[v{index}][a{index}]")
        filters.append("".join(concat_inputs) + f"concat=n={len(plan.clips)}:v=1:a=1[vout][aout]")
        args.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                output.video_codec,
                "-preset",
                output.preset,
                "-crf",
                str(output.crf),
                "-c:a",
                output.audio_codec,
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                "-pix_fmt",
                "yuv420p",
                str(temporary),
            ]
        )
        self.runner.run(args)
        os.replace(temporary, output.path)
        return output.path

    def burn_captions(self, video: Path, captions: Path) -> Path:
        """Burn an SRT into a rendered video using libass."""
        temporary = video.with_name(f".{video.stem}.captioned{video.suffix}")
        subtitle_path = str(captions.resolve()).replace("\\", "/")
        subtitle_path = subtitle_path.replace(":", r"\:").replace("'", r"\'")
        self.runner.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostdin",
                "-y",
                "-i",
                str(video),
                "-vf",
                f"subtitles=filename='{subtitle_path}'",
                "-c:v",
                "libx264",
                "-crf",
                "20",
                "-preset",
                "medium",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(temporary),
            ]
        )
        os.replace(temporary, video)
        return video
