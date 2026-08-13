"""A publisher that writes an inspectable manifest and performs no network I/O."""

from __future__ import annotations

import json
from pathlib import Path

from videoforge_agent.models import PublishingConfig, PublishResult


class DryRunPublisher:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def publish(self, video: str, config: PublishingConfig) -> PublishResult:
        self.workspace.mkdir(parents=True, exist_ok=True)
        manifest = self.workspace / "publication.preview.json"
        manifest.write_text(
            json.dumps(
                {
                    "video": video,
                    "requested_platform": config.platform,
                    "title": config.title,
                    "description": config.description,
                    "tags": config.tags,
                    "privacy": config.privacy,
                    "network_request_sent": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return PublishResult(platform=config.platform, status="dry-run", manifest=manifest)
