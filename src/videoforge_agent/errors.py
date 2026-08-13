"""Domain-specific errors with actionable messages."""


class VideoForgeError(RuntimeError):
    """Base error for expected VideoForge failures."""


class DependencyError(VideoForgeError):
    """A required external executable or optional package is missing."""


class MediaError(VideoForgeError):
    """Media probing, analysis, or rendering failed."""


class PublishError(VideoForgeError):
    """A publication could not be completed safely."""


class ApprovalRequiredError(PublishError):
    """Publishing was requested without both required approval signals."""
