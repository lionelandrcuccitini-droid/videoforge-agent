import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from videoforge_agent.errors import PublishError
from videoforge_agent.models import PublishingConfig
from videoforge_agent.publishers import create_publisher
from videoforge_agent.publishers.dry_run import DryRunPublisher
from videoforge_agent.publishers.webhook import WebhookPublisher
from videoforge_agent.publishers.youtube import YouTubePublisher


def test_dry_run_writes_manifest_without_network(tmp_path: Path) -> None:
    config = PublishingConfig(enabled=True, platform="dry-run", title="Demo")
    result = DryRunPublisher(tmp_path).publish("video.mp4", config)

    assert result.status == "dry-run"
    assert result.manifest is not None
    payload = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert payload["network_request_sent"] is False
    assert payload["title"] == "Demo"


def test_publisher_factory_defaults_to_dry_run(tmp_path: Path) -> None:
    publisher = create_publisher(PublishingConfig(), tmp_path)
    assert isinstance(publisher, DryRunPublisher)


def test_publisher_factory_selects_network_adapters(tmp_path: Path) -> None:
    webhook = create_publisher(PublishingConfig(platform="webhook"), tmp_path)
    youtube = create_publisher(PublishingConfig(platform="youtube"), tmp_path)

    assert isinstance(webhook, WebhookPublisher)
    assert isinstance(youtube, YouTubePublisher)


def test_webhook_requires_https_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("httpx")
    module.HTTPError = RuntimeError  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "httpx", module)
    monkeypatch.setenv("VIDEOFORGE_WEBHOOK_URL", "http://example.test/upload")

    with pytest.raises(PublishError, match="HTTPS URL"):
        WebhookPublisher().publish("video.mp4", PublishingConfig(platform="webhook"))


def test_webhook_publishes_and_reads_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    module = ModuleType("httpx")

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"id": "item-1", "url": "https://example.test/watch/item-1"}

    def post(*args: object, **kwargs: object) -> FakeResponse:
        del args, kwargs
        return FakeResponse()

    module.HTTPError = RuntimeError  # type: ignore[attr-defined]
    module.post = post  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "httpx", module)
    monkeypatch.setenv("VIDEOFORGE_WEBHOOK_URL", "https://example.test/upload")

    result = WebhookPublisher().publish(str(video), PublishingConfig(platform="webhook"))

    assert result.resource_id == "item-1"
    assert result.url == "https://example.test/watch/item-1"
