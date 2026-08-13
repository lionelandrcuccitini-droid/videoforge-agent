import json
from pathlib import Path

from videoforge_agent.models import PublishingConfig
from videoforge_agent.publishers import create_publisher
from videoforge_agent.publishers.dry_run import DryRunPublisher


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
