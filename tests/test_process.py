import subprocess

import pytest

from videoforge_agent.errors import MediaError
from videoforge_agent.process import CommandRunner


def test_command_runner_returns_captured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(["tool"], 0, stdout="ready", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    result = CommandRunner().run(["tool", "--check"])

    assert result.stdout == "ready"


def test_command_runner_reports_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    completed = subprocess.CompletedProcess(["tool"], 7, stdout="", stderr="bad input")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    with pytest.raises(MediaError, match="exit code 7"):
        CommandRunner().run(["tool"])


def test_command_runner_reports_missing_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*args: object, **kwargs: object) -> None:
        raise OSError("not found")

    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(MediaError, match="could not execute"):
        CommandRunner().run(["missing-tool"])
