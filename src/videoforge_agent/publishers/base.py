"""Publisher extension interface."""

from __future__ import annotations

from typing import Protocol

from videoforge_agent.models import PublishingConfig, PublishResult


class Publisher(Protocol):
    def publish(self, video: str, config: PublishingConfig) -> PublishResult:
        """Publish a rendered video or safely describe the intended action."""
