"""Recoverable orchestration for the complete video production workflow."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

from videoforge_agent.captions import WhisperTranscriber, write_srt
from videoforge_agent.errors import ApprovalRequiredError, DependencyError
from videoforge_agent.media import MediaAnalyzer
from videoforge_agent.models import EditPlan, ProjectConfig, RunResult, Scene
from videoforge_agent.planner import TimelinePlanner
from videoforge_agent.publishers import create_publisher
from videoforge_agent.renderer import FFmpegRenderer

ProgressCallback = Callable[[str, str], None]


def _silent_progress(stage: str, message: str) -> None:
    del stage, message


class VideoForgeAgent:
    """Analyze, plan, render, caption, and optionally publish one project."""

    def __init__(
        self,
        *,
        analyzer: MediaAnalyzer | None = None,
        planner: TimelinePlanner | None = None,
        renderer: FFmpegRenderer | None = None,
        transcriber: WhisperTranscriber | None = None,
        progress: ProgressCallback = _silent_progress,
    ) -> None:
        self.analyzer = analyzer or MediaAnalyzer()
        self.planner = planner or TimelinePlanner()
        self.renderer = renderer or FFmpegRenderer()
        self.transcriber = transcriber or WhisperTranscriber()
        self.progress = progress

    def run(
        self, config: ProjectConfig, *, approve_publish: bool = False, resume: bool = True
    ) -> RunResult:
        self._check_dependencies()
        config.workspace.mkdir(parents=True, exist_ok=True)
        plan_path = config.workspace / "edit-plan.json"

        if resume and plan_path.is_file():
            self.progress("plan", f"reusing {plan_path}")
            plan = EditPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
        else:
            scenes = self._analyze(config)
            self.progress("plan", "selecting clips")
            plan = self.planner.create(config, scenes)
            plan_path.write_text(
                plan.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8"
            )

        if resume and config.output.path.is_file():
            self.progress("render", f"reusing {config.output.path}")
            video = config.output.path
        else:
            self.progress("render", f"rendering {len(plan.clips)} clips")
            video = self.renderer.render(plan, config.output)

        captions: Path | None = None
        if config.captions.enabled:
            captions = config.workspace / "captions.srt"
            if not (resume and captions.is_file()):
                self.progress("captions", f"transcribing with {config.captions.model}")
                segments = self.transcriber.transcribe(video, config.captions)
                write_srt(segments, captions)
                if config.captions.burn_in:
                    self.progress("captions", "burning subtitles into video")
                    self.renderer.burn_captions(video, captions)

        publication = None
        if config.publishing.enabled:
            if not approve_publish:
                raise ApprovalRequiredError(
                    "render completed, but publishing needs the explicit --approve-publish flag"
                )
            self.progress("publish", f"publishing through {config.publishing.platform}")
            publisher = create_publisher(config.publishing, config.workspace)
            publication = publisher.publish(str(video), config.publishing)

        self.progress("done", str(video))
        return RunResult(
            plan=plan_path, video=video, captions=captions, publication=publication
        )

    def _analyze(self, config: ProjectConfig) -> list[Scene]:
        scenes: list[Scene] = []
        media_payload: list[dict[str, object]] = []
        for source in config.sources:
            self.progress("analyze", f"probing {source.name}")
            info = self.analyzer.probe(source)
            media_payload.append(info.model_dump(mode="json"))
            self.progress("analyze", f"detecting scenes in {source.name}")
            scenes.extend(self.analyzer.detect_scenes(info, config.selection))
        (config.workspace / "media.json").write_text(
            json.dumps(media_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (config.workspace / "scenes.json").write_text(
            json.dumps(
                [scene.model_dump(mode="json") for scene in scenes],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return scenes

    @staticmethod
    def _check_dependencies() -> None:
        missing = [command for command in ("ffmpeg", "ffprobe") if not shutil.which(command)]
        if missing:
            raise DependencyError(
                "missing external tools: "
                + ", ".join(missing)
                + ". Install FFmpeg or use the provided Docker image."
            )

