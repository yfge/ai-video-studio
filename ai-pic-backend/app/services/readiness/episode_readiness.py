"""
Episode readiness checker for pre-generation validation.

Extends story readiness checks with episode-specific validations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.script import Episode, Script, Story
from app.schemas.readiness import ReadinessCheck, ReadinessResult
from app.services.readiness.story_readiness import StoryReadinessChecker

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class EpisodeReadinessChecker:
    """Validates episode readiness for script generation."""

    def __init__(self, db: "Session"):
        self.db = db
        self.story_checker = StoryReadinessChecker(db)

    def check(self, story: Story, episode: Episode) -> ReadinessResult:
        """Run story + episode readiness checks."""
        # First run story checks
        story_result = self.story_checker.check(story)
        checks = list(story_result.checks)

        # Add episode-specific checks
        checks.extend(self._check_episode_exists(episode))
        checks.extend(self._check_story_matches(story, episode))
        checks.extend(self._check_previous_episodes(story, episode))

        # Recalculate readiness status
        has_critical = any(
            not c.passed and c.severity == "CRITICAL" for c in checks
        )
        has_errors = any(not c.passed and c.severity == "ERROR" for c in checks)

        can_proceed = not has_critical
        ready = can_proceed and not has_errors

        # Build summary
        summary = self._build_summary(checks, ready, can_proceed, episode)

        return ReadinessResult(
            ready=ready,
            can_proceed=can_proceed,
            story_id=story.id,
            episode_id=episode.id,
            checks=checks,
            summary=summary,
        )

    def _check_episode_exists(self, episode: Episode) -> list[ReadinessCheck]:
        """Check that episode exists and is not deleted (CRITICAL)."""
        checks = []

        exists = episode is not None and not getattr(episode, "is_deleted", False)
        checks.append(
            ReadinessCheck(
                name="episode_exists",
                passed=exists,
                severity="CRITICAL",
                message=(
                    f"Episode #{episode.episode_number}: {episode.title}"
                    if exists
                    else "Episode not found or deleted"
                ),
                suggestion=None if exists else "Ensure episode exists and is not deleted",
            )
        )

        return checks

    def _check_story_matches(
        self, story: Story, episode: Episode
    ) -> list[ReadinessCheck]:
        """Check that episode belongs to the target story (CRITICAL)."""
        checks = []

        matches = episode.story_id == story.id
        checks.append(
            ReadinessCheck(
                name="story_matches",
                passed=matches,
                severity="CRITICAL",
                message=(
                    "Episode belongs to the correct story"
                    if matches
                    else f"Episode story_id ({episode.story_id}) != target story ({story.id})"
                ),
                suggestion=(
                    None
                    if matches
                    else "Ensure episode is associated with the correct story"
                ),
            )
        )

        return checks

    def _check_previous_episodes(
        self, story: Story, episode: Episode
    ) -> list[ReadinessCheck]:
        """Check if earlier episodes have scripts (WARNING for continuity)."""
        checks = []

        # Get earlier episodes
        earlier_episodes = (
            self.db.query(Episode)
            .filter(
                Episode.story_id == story.id,
                Episode.episode_number < episode.episode_number,
                Episode.is_deleted.is_(False),
            )
            .all()
        )

        if not earlier_episodes:
            # First episode, no continuity check needed
            return checks

        # Check which earlier episodes have scripts
        earlier_ids = [e.id for e in earlier_episodes]
        episodes_with_scripts = (
            self.db.query(Script.episode_id)
            .filter(
                Script.episode_id.in_(earlier_ids),
                Script.is_deleted.is_(False),
            )
            .distinct()
            .all()
        )
        episodes_with_scripts_set = {e.episode_id for e in episodes_with_scripts}

        missing_scripts = [
            e.episode_number
            for e in earlier_episodes
            if e.id not in episodes_with_scripts_set
        ]

        all_complete = len(missing_scripts) == 0
        checks.append(
            ReadinessCheck(
                name="previous_episodes_complete",
                passed=all_complete,
                severity="WARNING",
                message=(
                    f"All {len(earlier_episodes)} previous episode(s) have scripts"
                    if all_complete
                    else f"Episodes {missing_scripts} missing scripts (may affect continuity)"
                ),
                suggestion=(
                    None
                    if all_complete
                    else "Generate scripts for earlier episodes first for better continuity"
                ),
            )
        )

        return checks

    def _build_summary(
        self,
        checks: list[ReadinessCheck],
        ready: bool,
        can_proceed: bool,
        episode: Episode,
    ) -> str:
        """Build human-readable summary for episode readiness."""
        failed = [c for c in checks if not c.passed]
        episode_info = f"Episode #{episode.episode_number}"

        if not failed:
            return f"{episode_info}: All readiness checks passed"

        critical = sum(1 for c in failed if c.severity == "CRITICAL")
        errors = sum(1 for c in failed if c.severity == "ERROR")
        warnings = sum(1 for c in failed if c.severity == "WARNING")

        parts = []
        if critical:
            parts.append(f"{critical} critical issue(s)")
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")

        status = (
            "Ready"
            if ready
            else ("Can proceed with caution" if can_proceed else "Not ready")
        )
        return f"{episode_info} - {status}: {', '.join(parts)}"
