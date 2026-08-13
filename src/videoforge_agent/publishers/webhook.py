"""Generic multipart webhook publisher for a user-controlled endpoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from videoforge_agent.errors import DependencyError, PublishError
from videoforge_agent.models import PublishResult, PublishingConfig


class WebhookPublisher:
    def publish(self, video: str, config: PublishingConfig) -> PublishResult:
        try:
            import httpx
        except ImportError as exc:
            raise DependencyError(
                "webhook publishing requires: python -m pip install 'videoforge-agent[webhook]'"
            ) from exc
        endpoint = os.environ.get("VIDEOFORGE_WEBHOOK_URL")
        if not endpoint or not endpoint.lower().startswith("https://"):
            raise PublishError("VIDEOFORGE_WEBHOOK_URL must be an HTTPS URL")
        metadata = config.model_dump(mode="json")
        path = Path(video)
        try:
            with path.open("rb") as stream:
                response = httpx.post(
                    endpoint,
                    data={"metadata": json.dumps(metadata, ensure_ascii=False)},
                    files={"video": (path.name, stream, "video/mp4")},
                    timeout=600,
                    follow_redirects=False,
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PublishError(f"webhook upload failed: {exc}") from exc
        try:
            payload: dict[str, Any] = response.json()
        except ValueError:
            payload = {}
        return PublishResult(
            platform="webhook",
            status="published",
            resource_id=str(payload.get("id")) if payload.get("id") else None,
            url=str(payload.get("url")) if payload.get("url") else None,
        )
