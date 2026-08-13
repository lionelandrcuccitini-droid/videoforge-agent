"""YouTube Data API v3 resumable upload publisher."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from videoforge_agent.errors import DependencyError, PublishError
from videoforge_agent.models import PublishResult, PublishingConfig


class YouTubePublisher:
    def publish(self, video: str, config: PublishingConfig) -> PublishResult:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise DependencyError(
                "YouTube publishing requires: python -m pip install 'videoforge-agent[youtube]'"
            ) from exc

        secrets = Path(
            os.environ.get("VIDEOFORGE_YOUTUBE_CLIENT_SECRETS", "client_secret.json")
        )
        token = Path(os.environ.get("VIDEOFORGE_YOUTUBE_TOKEN", "youtube.token.json"))
        if not secrets.is_file():
            raise PublishError(f"YouTube OAuth client secrets not found: {secrets}")
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        credentials: Any = None
        if token.is_file():
            credentials = Credentials.from_authorized_user_file(str(token), scopes)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets), scopes)
            credentials = flow.run_local_server(port=0)
        token.parent.mkdir(parents=True, exist_ok=True)
        token.write_text(credentials.to_json(), encoding="utf-8")

        service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        body = {
            "snippet": {
                "title": config.title,
                "description": config.description,
                "tags": config.tags,
            },
            "status": {"privacyStatus": config.privacy, "selfDeclaredMadeForKids": False},
        }
        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaFileUpload(video, chunksize=-1, resumable=True),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = str(response["id"])
        return PublishResult(
            platform="youtube",
            status="published",
            resource_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
        )

