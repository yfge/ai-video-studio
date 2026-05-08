"""Environment-aware readiness wrappers for API-facing checks."""

from __future__ import annotations

from app.models.script import Episode, Story
from app.schemas.readiness import ReadinessResult
from app.services.readiness.environment_readiness import EnvironmentReadinessAugmentor
from app.services.readiness.episode_readiness import (
    EpisodeReadinessChecker as BaseEpisodeReadinessChecker,
)
from app.services.readiness.story_readiness import (
    StoryReadinessChecker as BaseStoryReadinessChecker,
)


class StoryReadinessChecker(BaseStoryReadinessChecker):
    def check(self, story: Story) -> ReadinessResult:
        result = super().check(story)
        return EnvironmentReadinessAugmentor(self.db).apply(result, story)


class EpisodeReadinessChecker(BaseEpisodeReadinessChecker):
    def check(self, story: Story, episode: Episode) -> ReadinessResult:
        result = super().check(story, episode)
        return EnvironmentReadinessAugmentor(self.db).apply(
            result, story, episode_number=episode.episode_number
        )
