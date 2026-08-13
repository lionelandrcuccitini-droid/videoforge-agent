"""VideoForge Agent public package."""

from videoforge_agent.agent import VideoForgeAgent
from videoforge_agent.models import EditPlan, ProjectConfig

__all__ = ["EditPlan", "ProjectConfig", "VideoForgeAgent"]
__version__ = "0.1.0"
