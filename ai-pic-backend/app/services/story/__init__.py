__all__ = ["StoryGenerationService"]


def __getattr__(name: str):
    if name == "StoryGenerationService":
        from .story_generation_service import StoryGenerationService

        return StoryGenerationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
