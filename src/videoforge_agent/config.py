"""Project configuration loading and path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from videoforge_agent.models import ProjectConfig


def _resolve(base: Path, value: Path) -> Path:
    return value if value.is_absolute() else (base / value).resolve()


def load_config(path: Path) -> ProjectConfig:
    """Load YAML and make every media/artifact path relative to that YAML file."""
    config_path = path.resolve()
    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("project config must be a YAML mapping")
    config = ProjectConfig.model_validate(raw)
    base = config_path.parent
    resolved_sources = [_resolve(base, source) for source in config.sources]
    missing = [str(source) for source in resolved_sources if not source.is_file()]
    if missing:
        raise FileNotFoundError("source files do not exist: " + ", ".join(missing))
    return config.model_copy(
        update={
            "sources": resolved_sources,
            "workspace": _resolve(base, config.workspace),
            "output": config.output.model_copy(
                update={"path": _resolve(base, config.output.path)}
            ),
        }
    )
