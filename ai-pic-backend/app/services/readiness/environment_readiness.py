"""Environment readiness checks appended to story and episode readiness."""

from __future__ import annotations

from app.models.script import Story
from app.repositories.story_environment_readiness_repository import (
    StoryEnvironmentReadinessRepository,
)
from app.schemas.readiness import ReadinessCheck, ReadinessResult
from sqlalchemy.orm import Session


class EnvironmentReadinessAugmentor:
    def __init__(self, db: Session):
        self.repository = StoryEnvironmentReadinessRepository(db)

    def apply(
        self, result: ReadinessResult, story: Story, *, episode_number: int | None = None
    ) -> ReadinessResult:
        checks = [*result.checks, *self._build_checks(story)]
        ready, can_proceed = self._status(checks)
        return result.model_copy(
            update={
                "checks": checks,
                "ready": ready,
                "can_proceed": can_proceed,
                "summary": self._summary(
                    checks,
                    ready,
                    can_proceed,
                    result,
                    episode_number=episode_number,
                ),
            }
        )

    def _build_checks(self, story: Story) -> list[ReadinessCheck]:
        virtual_ip_ids = self.repository.list_story_virtual_ip_ids(story.id)
        if not virtual_ip_ids:
            return []

        linked_env_count = self.repository.count_linked_environments(virtual_ip_ids)
        checks = [
            ReadinessCheck(
                name="ip_environment_pool_linked",
                passed=linked_env_count > 0,
                severity="WARNING",
                message=(
                    f"IP environment pool has {linked_env_count} linked asset(s)"
                    if linked_env_count > 0
                    else "No environments linked to story IPs"
                ),
                suggestion=(
                    None
                    if linked_env_count > 0
                    else "Link reusable environments from the IP detail asset panel"
                ),
            )
        ]

        coverage = self.repository.get_scene_environment_coverage(
            self.repository.list_story_script_ids(story.id)
        )
        if coverage:
            checks.append(
                ReadinessCheck(
                    name="scene_environment_coverage",
                    passed=coverage.bound == coverage.total,
                    severity="WARNING",
                    message=(
                        f"Scene environment coverage: {coverage.bound}/{coverage.total}"
                    ),
                    suggestion=(
                        None
                        if coverage.bound == coverage.total
                        else "Bind environments in the episode Timeline inspector"
                    ),
                )
            )
        return checks

    def _status(self, checks: list[ReadinessCheck]) -> tuple[bool, bool]:
        has_critical = any(
            not check.passed and check.severity == "CRITICAL" for check in checks
        )
        has_errors = any(
            not check.passed and check.severity == "ERROR" for check in checks
        )
        can_proceed = not has_critical
        return can_proceed and not has_errors, can_proceed

    def _summary(
        self,
        checks: list[ReadinessCheck],
        ready: bool,
        can_proceed: bool,
        result: ReadinessResult,
        *,
        episode_number: int | None = None,
    ) -> str:
        failed = [check for check in checks if not check.passed]
        if not failed:
            return result.summary

        parts = []
        for severity, label in (
            ("CRITICAL", "critical issue(s)"),
            ("ERROR", "error(s)"),
            ("WARNING", "warning(s)"),
        ):
            count = sum(1 for check in failed if check.severity == severity)
            if count:
                parts.append(f"{count} {label}")

        status = (
            "Ready" if ready else ("Can proceed with caution" if can_proceed else "Not ready")
        )
        prefix = f"Episode #{episode_number} - " if episode_number else ""
        return f"{prefix}{status}: {', '.join(parts)}"
