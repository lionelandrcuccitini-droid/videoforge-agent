"""VideoForge command-line interface."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from videoforge_agent import __version__
from videoforge_agent.agent import VideoForgeAgent
from videoforge_agent.config import load_config
from videoforge_agent.errors import VideoForgeError

app = typer.Typer(
    name="videoforge",
    help="Automatic, reviewable video editing and publishing.",
    no_args_is_help=True,
)
console = Console()


def _version(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version, is_eager=True, help="Show the version."
    ),
) -> None:
    """Build repeatable video workflows from a YAML project file."""
    del version


def _progress(stage: str, message: str) -> None:
    console.print(f"[bold cyan]{stage:>8}[/bold cyan]  {message}")


@app.command()
def validate(project: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate a project and verify all source files."""
    try:
        config = load_config(project)
    except (OSError, ValueError, ValidationError) as exc:
        console.print(f"[bold red]Invalid project:[/bold red] {exc}", highlight=False)
        raise typer.Exit(code=2) from exc
    console.print(
        f"[green]Valid[/green] {config.name}: {len(config.sources)} source(s), "
        f"target {config.selection.target_duration:g}s"
    )


@app.command()
def plan(
    project: Path = typer.Argument(..., exists=True, dir_okay=False),
    force: bool = typer.Option(False, "--force", help="Replace an existing edit plan."),
) -> None:
    """Analyze sources and write an edit plan without rendering."""
    try:
        config = load_config(project)
        agent = VideoForgeAgent(progress=_progress)
        agent._check_dependencies()
        config.workspace.mkdir(parents=True, exist_ok=True)
        plan_path = config.workspace / "edit-plan.json"
        if plan_path.exists() and not force:
            console.print(f"[yellow]Plan already exists:[/yellow] {plan_path}")
            raise typer.Exit(code=2)
        edit_plan = agent.planner.create(config, agent._analyze(config))
        plan_path.write_text(edit_plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Plan ready:[/green] {plan_path}")
    except VideoForgeError as exc:
        console.print(f"[bold red]Planning failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def run(
    project: Path = typer.Argument(..., exists=True, dir_okay=False),
    approve_publish: bool = typer.Option(
        False,
        "--approve-publish",
        help="Second confirmation required before any publishing adapter runs.",
    ),
    no_resume: bool = typer.Option(False, help="Re-analyze and re-render every stage."),
) -> None:
    """Run analysis, planning, rendering, captions, and optional publishing."""
    try:
        config = load_config(project)
        result = VideoForgeAgent(progress=_progress).run(
            config, approve_publish=approve_publish, resume=not no_resume
        )
    except (OSError, ValueError, ValidationError, VideoForgeError) as exc:
        console.print(f"[bold red]Run failed:[/bold red] {exc}", highlight=False)
        raise typer.Exit(code=1) from exc
    console.print_json(json.dumps(result.model_dump(mode="json"), ensure_ascii=False))


@app.command()
def doctor() -> None:
    """Check required and optional runtime capabilities."""
    table = Table(title="VideoForge environment")
    table.add_column("Capability")
    table.add_column("Status")
    table.add_row("Python", sys.version.split()[0])
    for executable in ("ffmpeg", "ffprobe"):
        location = shutil.which(executable)
        table.add_row(executable, f"[green]{location}[/green]" if location else "[red]missing[/red]")
    for module, extra in (
        ("faster_whisper", "transcribe"),
        ("googleapiclient", "youtube"),
        ("httpx", "webhook"),
    ):
        try:
            __import__(module)
            state = "[green]installed[/green]"
        except ImportError:
            state = f"optional: pip install 'videoforge-agent[{extra}]'"
        table.add_row(module, state)
    console.print(table)


if __name__ == "__main__":
    app()
