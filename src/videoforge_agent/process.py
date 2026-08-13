"""Safe subprocess execution without a command shell."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from videoforge_agent.errors import MediaError


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str


class CommandRunner:
    """Execute argv lists and surface a redacted, bounded failure message."""

    def run(self, args: Sequence[str], *, cwd: Path | None = None) -> CommandResult:
        try:
            completed = subprocess.run(
                list(args),
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise MediaError(f"could not execute {args[0]!r}: {exc}") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout)[-4000:]
            raise MediaError(f"{args[0]} failed with exit code {completed.returncode}:\n{detail}")
        return CommandResult(completed.stdout, completed.stderr)
