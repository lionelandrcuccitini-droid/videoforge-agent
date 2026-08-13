"""Built-in publisher adapters."""

from pathlib import Path

from videoforge_agent.models import PublishingConfig
from videoforge_agent.publishers.base import Publisher
from videoforge_agent.publishers.dry_run import DryRunPublisher
from videoforge_agent.publishers.webhook import WebhookPublisher
from videoforge_agent.publishers.youtube import YouTubePublisher


def create_publisher(config: PublishingConfig, workspace: Path) -> Publisher:
    if config.platform == "youtube":
        return YouTubePublisher()
    if config.platform == "webhook":
        return WebhookPublisher()
    return DryRunPublisher(workspace)


__all__ = ["DryRunPublisher", "Publisher", "create_publisher"]
