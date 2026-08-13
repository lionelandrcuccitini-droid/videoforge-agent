from pathlib import Path

import pytest
from pydantic import ValidationError

from videoforge_agent.config import load_config
from videoforge_agent.models import ProjectConfig, SelectionConfig


def test_load_config_resolves_paths(tmp_path: Path) -> None:
    source = tmp_path / "input.mp4"
    source.touch()
    project = tmp_path / "project.yml"
    project.write_text(
        """\
version: 1
name: demo
sources: [input.mp4]
workspace: work
output:
  path: artifacts/out.mp4
""",
        encoding="utf-8",
    )

    config = load_config(project)

    assert config.sources == [source]
    assert config.workspace == tmp_path / "work"
    assert config.output.path == tmp_path / "artifacts" / "out.mp4"


def test_load_config_rejects_missing_sources(tmp_path: Path) -> None:
    project = tmp_path / "project.yml"
    project.write_text(
        "version: 1\nname: demo\nsources: [missing.mp4]\n", encoding="utf-8"
    )

    with pytest.raises(FileNotFoundError, match=r"missing\.mp4"):
        load_config(project)


def test_load_config_reports_invalid_yaml(tmp_path: Path) -> None:
    project = tmp_path / "project.yml"
    project.write_text("name: [unterminated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid YAML"):
        load_config(project)


def test_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate(
            {"version": 1, "name": "demo", "sources": ["a.mp4"], "surprise": True}
        )


def test_selection_validates_duration_order() -> None:
    with pytest.raises(ValidationError, match="max_scene_duration"):
        SelectionConfig(min_scene_duration=5, max_scene_duration=2)
