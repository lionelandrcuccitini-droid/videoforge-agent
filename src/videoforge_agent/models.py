"""Validated configuration, timeline, and result models."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Forbid misspelled configuration fields instead of silently ignoring them."""

    model_config = ConfigDict(extra="forbid")


class OutputConfig(StrictModel):
    path: Path = Path("artifacts/output.mp4")
    width: int = Field(default=1920, ge=16, le=7680)
    height: int = Field(default=1080, ge=16, le=4320)
    fps: int = Field(default=30, ge=1, le=120)
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = Field(default=20, ge=0, le=51)
    preset: str = "medium"


class SelectionConfig(StrictModel):
    target_duration: float = Field(default=60, gt=0, le=21600)
    min_scene_duration: float = Field(default=1.0, gt=0, le=60)
    max_scene_duration: float = Field(default=10.0, gt=0, le=600)
    scene_threshold: float = Field(default=0.32, gt=0, lt=1)

    @model_validator(mode="after")
    def duration_order(self) -> SelectionConfig:
        if self.max_scene_duration < self.min_scene_duration:
            raise ValueError("max_scene_duration must be >= min_scene_duration")
        return self


class CaptionConfig(StrictModel):
    enabled: bool = False
    backend: Literal["faster-whisper"] = "faster-whisper"
    model: str = "large-v3-turbo"
    language: str | None = None
    burn_in: bool = False


class PublishingConfig(StrictModel):
    enabled: bool = False
    platform: Literal["dry-run", "youtube", "webhook"] = "dry-run"
    title: str = Field(default="VideoForge video", min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list)
    privacy: Literal["private", "unlisted", "public"] = "private"


class ProjectConfig(StrictModel):
    version: Literal[1] = 1
    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    sources: list[Path] = Field(min_length=1)
    workspace: Path = Path("workspace/default")
    output: OutputConfig = Field(default_factory=OutputConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    captions: CaptionConfig = Field(default_factory=CaptionConfig)
    publishing: PublishingConfig = Field(default_factory=PublishingConfig)

    @field_validator("sources")
    @classmethod
    def unique_sources(cls, value: list[Path]) -> list[Path]:
        normalized = [str(path).casefold() for path in value]
        if len(set(normalized)) != len(value):
            raise ValueError("sources must not contain duplicates")
        return value


class MediaInfo(StrictModel):
    path: Path
    duration: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: float = Field(gt=0)
    has_audio: bool


class Scene(StrictModel):
    source: Path
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    has_audio: bool = True
    score: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def valid_range(self) -> Scene:
        if self.end <= self.start:
            raise ValueError("scene end must be greater than start")
        return self

    @property
    def duration(self) -> float:
        return self.end - self.start


class EditPlan(StrictModel):
    version: Literal[1] = 1
    project: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    clips: list[Scene] = Field(min_length=1)
    target_duration: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)

    @property
    def duration(self) -> float:
        return sum(clip.duration for clip in self.clips)


class CaptionSegment(StrictModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(min_length=1)


class PublishResult(StrictModel):
    platform: str
    status: Literal["dry-run", "published"]
    resource_id: str | None = None
    url: str | None = None
    manifest: Path | None = None


class RunResult(StrictModel):
    plan: Path
    video: Path
    captions: Path | None = None
    publication: PublishResult | None = None

