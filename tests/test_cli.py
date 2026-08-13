from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from videoforge_agent.cli import app
from videoforge_agent.errors import DependencyError
from videoforge_agent.models import EditPlan, RunResult, Scene

runner = CliRunner()


def write_project(tmp_path: Path) -> Path:
    (tmp_path / "input.mp4").touch()
    project = tmp_path / "project.yml"
    project.write_text(
        "version: 1\nname: demo\nsources: [input.mp4]\nworkspace: work\n",
        encoding="utf-8",
    )
    return project


def test_version_and_doctor_commands() -> None:
    version = runner.invoke(app, ["--version"])
    doctor = runner.invoke(app, ["doctor"])

    assert version.exit_code == 0
    assert "0.1.0" in version.output
    assert doctor.exit_code == 0
    assert "VideoForge environment" in doctor.output


def test_validate_accepts_valid_project_and_rejects_missing_source(tmp_path: Path) -> None:
    project = write_project(tmp_path)
    valid = runner.invoke(app, ["validate", str(project)])

    project.write_text(
        "version: 1\nname: demo\nsources: [missing.mp4]\n",
        encoding="utf-8",
    )
    invalid = runner.invoke(app, ["validate", str(project)])

    assert valid.exit_code == 0
    assert "Valid demo" in valid.output
    assert invalid.exit_code == 2
    assert "Invalid project" in invalid.output


def test_plan_writes_reviewable_edit_plan(tmp_path: Path) -> None:
    project = write_project(tmp_path)
    source = (tmp_path / "input.mp4").resolve()
    edit_plan = EditPlan(
        project="demo",
        clips=[Scene(source=source, start=0, end=1)],
        target_duration=1,
        width=1920,
        height=1080,
        fps=30,
    )
    agent = Mock()
    agent._analyze.return_value = []
    agent.planner.create.return_value = edit_plan

    with patch("videoforge_agent.cli.VideoForgeAgent", return_value=agent):
        result = runner.invoke(app, ["plan", str(project)])

    assert result.exit_code == 0
    assert (tmp_path / "work" / "edit-plan.json").is_file()
    agent._check_dependencies.assert_called_once_with()


def test_run_prints_result_and_reports_expected_failure(tmp_path: Path) -> None:
    project = write_project(tmp_path)
    run_result = RunResult(plan=tmp_path / "plan.json", video=tmp_path / "video.mp4")
    agent = Mock()
    agent.run.return_value = run_result

    with patch("videoforge_agent.cli.VideoForgeAgent", return_value=agent):
        success = runner.invoke(app, ["run", str(project), "--no-resume"])

    agent.run.side_effect = DependencyError("ffmpeg missing")
    with patch("videoforge_agent.cli.VideoForgeAgent", return_value=agent):
        failure = runner.invoke(app, ["run", str(project)])

    assert success.exit_code == 0
    assert "video.mp4" in success.output
    assert failure.exit_code == 1
    assert "Run failed" in failure.output
