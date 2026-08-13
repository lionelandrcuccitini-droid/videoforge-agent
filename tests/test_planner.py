from pathlib import Path

import pytest

from videoforge_agent.models import ProjectConfig, Scene, SelectionConfig
from videoforge_agent.planner import TimelinePlanner


def config(target: float = 6) -> ProjectConfig:
    return ProjectConfig(
        version=1,
        name="demo",
        sources=[Path("a.mp4")],
        selection=SelectionConfig(target_duration=target, min_scene_duration=1),
    )


def test_planner_trims_last_clip_and_preserves_timeline_order() -> None:
    scenes = [
        Scene(source=Path("a.mp4"), start=5, end=10, score=0.9),
        Scene(source=Path("a.mp4"), start=0, end=5, score=1.0),
    ]

    plan = TimelinePlanner().create(config(), scenes)

    assert plan.duration == pytest.approx(6)
    assert [(item.start, item.end) for item in plan.clips] == [(0, 5), (5, 6)]


def test_planner_rejects_empty_scene_list() -> None:
    with pytest.raises(ValueError, match="no scenes"):
        TimelinePlanner().create(config(), [])

