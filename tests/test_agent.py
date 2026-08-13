from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from videoforge_agent.agent import VideoForgeAgent
from videoforge_agent.errors import ApprovalRequiredError
from videoforge_agent.models import (
    MediaInfo,
    OutputConfig,
    ProjectConfig,
    PublishingConfig,
    Scene,
    SelectionConfig,
)
from videoforge_agent.publishers.dry_run import DryRunPublisher


def make_config(tmp_path: Path, *, publishing: bool = False) -> ProjectConfig:
    source = tmp_path / "source.mp4"
    source.touch()
    return ProjectConfig(
        version=1,
        name="demo",
        sources=[source],
        workspace=tmp_path / "work",
        output=OutputConfig(path=tmp_path / "out.mp4"),
        selection=SelectionConfig(target_duration=2),
        publishing=PublishingConfig(enabled=publishing, platform="dry-run"),
    )


def test_agent_writes_plan_renders_and_resumes(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    info = MediaInfo(
        path=config.sources[0], duration=3, width=10, height=10, fps=30, has_audio=True
    )
    analyzer = Mock()
    analyzer.probe.return_value = info
    analyzer.detect_scenes.return_value = [
        Scene(source=config.sources[0], start=0, end=3, has_audio=True)
    ]
    renderer = Mock()
    renderer.render.side_effect = lambda plan, output: output.path.touch() or output.path
    agent = VideoForgeAgent(analyzer=analyzer, renderer=renderer)

    with patch.object(agent, "_check_dependencies"):
        first = agent.run(config)
        second = agent.run(config)

    assert first.plan.is_file()
    assert first.video.is_file()
    assert second.video == first.video
    assert analyzer.probe.call_count == 1
    assert renderer.render.call_count == 1


def test_agent_requires_second_publish_approval_after_render(tmp_path: Path) -> None:
    config = make_config(tmp_path, publishing=True)
    info = MediaInfo(
        path=config.sources[0], duration=2, width=10, height=10, fps=30, has_audio=True
    )
    analyzer = Mock()
    analyzer.probe.return_value = info
    analyzer.detect_scenes.return_value = [
        Scene(source=config.sources[0], start=0, end=2, has_audio=True)
    ]
    renderer = Mock()
    renderer.render.side_effect = lambda plan, output: output.path.touch() or output.path
    agent = VideoForgeAgent(analyzer=analyzer, renderer=renderer)

    with (
        patch.object(agent, "_check_dependencies"),
        pytest.raises(ApprovalRequiredError, match="--approve-publish"),
    ):
        agent.run(config)

    assert config.output.path.is_file()


def test_agent_checkpoints_publication_to_prevent_duplicate_uploads(tmp_path: Path) -> None:
    config = make_config(tmp_path, publishing=True)
    info = MediaInfo(
        path=config.sources[0], duration=2, width=10, height=10, fps=30, has_audio=True
    )
    analyzer = Mock()
    analyzer.probe.return_value = info
    analyzer.detect_scenes.return_value = [
        Scene(source=config.sources[0], start=0, end=2, has_audio=True)
    ]
    renderer = Mock()
    renderer.render.side_effect = lambda plan, output: output.path.touch() or output.path
    publisher = DryRunPublisher(config.workspace)
    agent = VideoForgeAgent(analyzer=analyzer, renderer=renderer)

    with (
        patch.object(agent, "_check_dependencies"),
        patch("videoforge_agent.agent.create_publisher", return_value=publisher) as factory,
    ):
        first = agent.run(config, approve_publish=True)
        second = agent.run(config, approve_publish=False)

    assert first.publication is not None
    assert second.publication == first.publication
    assert (config.workspace / "publication.json").is_file()
    factory.assert_called_once()
