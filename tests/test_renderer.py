from pathlib import Path

from videoforge_agent.models import EditPlan, OutputConfig, Scene
from videoforge_agent.process import CommandResult
from videoforge_agent.renderer import FFmpegRenderer


class RecordingRunner:
    def __init__(self) -> None:
        self.args: list[str] = []

    def run(self, args: list[str], *, cwd: Path | None = None) -> CommandResult:
        del cwd
        self.args = args
        Path(args[-1]).touch()
        return CommandResult("", "")


def test_renderer_builds_one_concat_graph_and_replaces_atomically(tmp_path: Path) -> None:
    runner = RecordingRunner()
    renderer = FFmpegRenderer(runner)  # type: ignore[arg-type]
    output = OutputConfig(path=tmp_path / "result.mp4", width=1080, height=1920, fps=30)
    plan = EditPlan(
        project="demo",
        clips=[
            Scene(source=Path("a.mp4"), start=0, end=2, has_audio=True),
            Scene(source=Path("b.mp4"), start=1, end=4, has_audio=False),
        ],
        target_duration=5,
        width=1080,
        height=1920,
        fps=30,
    )

    result = renderer.render(plan, output)

    graph = runner.args[runner.args.index("-filter_complex") + 1]
    assert "concat=n=2:v=1:a=1" in graph
    assert "anullsrc" in graph
    assert "crop=1080:1920" in graph
    assert result.is_file()


def test_renderer_burns_captions_and_replaces_video(tmp_path: Path) -> None:
    runner = RecordingRunner()
    renderer = FFmpegRenderer(runner)  # type: ignore[arg-type]
    video = tmp_path / "video.mp4"
    captions = tmp_path / "captions.srt"
    video.touch()
    captions.write_text("captions", encoding="utf-8")

    result = renderer.burn_captions(video, captions)

    assert result == video
    assert "subtitles=filename=" in runner.args[runner.args.index("-vf") + 1]
    assert video.is_file()
