"""Deterministic edit-decision planner."""

from __future__ import annotations

from videoforge_agent.models import EditPlan, ProjectConfig, Scene


class TimelinePlanner:
    """Choose scene-aligned clips up to the requested duration.

    The planner is deliberately deterministic. More advanced ranking models can
    produce scored ``Scene`` objects without changing the review/render contract.
    """

    def create(self, config: ProjectConfig, scenes: list[Scene]) -> EditPlan:
        if not scenes:
            raise ValueError("no scenes satisfy the selection constraints")
        chosen: list[Scene] = []
        remaining = config.selection.target_duration
        for scene in sorted(scenes, key=lambda item: item.score, reverse=True):
            if remaining <= 0:
                break
            if scene.duration <= remaining:
                chosen.append(scene)
                remaining -= scene.duration
            elif remaining >= config.selection.min_scene_duration:
                chosen.append(scene.model_copy(update={"end": scene.start + remaining}))
                remaining = 0
        chosen.sort(key=lambda item: (config.sources.index(item.source), item.start))
        if not chosen:
            raise ValueError("target duration is shorter than every allowed scene")
        return EditPlan(
            project=config.name,
            clips=chosen,
            target_duration=config.selection.target_duration,
            width=config.output.width,
            height=config.output.height,
            fps=config.output.fps,
        )
