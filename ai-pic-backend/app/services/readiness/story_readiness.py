"""
Story readiness checker for pre-generation validation.

Validates that a story has all required data before episode/script
generation can proceed.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.schemas.readiness import ReadinessCheck, ReadinessResult

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class StoryReadinessChecker:
    """Validates story readiness for generation."""

    def __init__(self, db: "Session"):
        self.db = db

    def check(self, story: Story) -> ReadinessResult:
        """Run all story readiness checks."""
        checks: list[ReadinessCheck] = []

        # Critical checks
        checks.extend(self._check_required_fields(story))

        # Error-level checks
        checks.extend(self._check_characters(story))

        # Warning-level checks
        checks.extend(self._check_marketing_meta(story))
        checks.extend(self._check_content_quality(story))

        # Info-level checks
        checks.extend(self._check_optional_content(story))

        # Calculate readiness status
        has_critical = any(
            not c.passed and c.severity == "CRITICAL" for c in checks
        )
        has_errors = any(not c.passed and c.severity == "ERROR" for c in checks)

        can_proceed = not has_critical
        ready = can_proceed and not has_errors

        # Build summary
        summary = self._build_summary(checks, ready, can_proceed)

        return ReadinessResult(
            ready=ready,
            can_proceed=can_proceed,
            story_id=story.id,
            episode_id=None,
            checks=checks,
            summary=summary,
        )

    def _check_required_fields(self, story: Story) -> list[ReadinessCheck]:
        """Check CRITICAL required fields."""
        checks = []

        # Title check
        has_title = bool(story.title and story.title.strip())
        checks.append(
            ReadinessCheck(
                name="title_present",
                passed=has_title,
                severity="CRITICAL",
                message="Title is set" if has_title else "Story title is missing",
                suggestion=None if has_title else "Add a story title",
            )
        )

        # Genre check
        has_genre = bool(story.genre and story.genre.strip())
        checks.append(
            ReadinessCheck(
                name="genre_present",
                passed=has_genre,
                severity="CRITICAL",
                message="Genre is set" if has_genre else "Story genre is missing",
                suggestion=None if has_genre else "Select a genre for the story",
            )
        )

        return checks

    def _check_characters(self, story: Story) -> list[ReadinessCheck]:
        """Check character requirements (CRITICAL and ERROR)."""
        checks = []

        # Get story characters
        story_characters = (
            self.db.query(StoryCharacter)
            .filter(
                StoryCharacter.story_id == story.id,
                StoryCharacter.is_deleted.is_(False),
            )
            .all()
        )

        # Has at least one character (CRITICAL)
        has_characters = len(story_characters) > 0
        checks.append(
            ReadinessCheck(
                name="has_characters",
                passed=has_characters,
                severity="CRITICAL",
                message=(
                    f"Story has {len(story_characters)} character(s)"
                    if has_characters
                    else "No characters linked to story"
                ),
                suggestion=(
                    None if has_characters else "Add at least one character to the story"
                ),
            )
        )

        if not story_characters:
            return checks

        # Check if virtual_ip references are valid (ERROR)
        virtual_ip_ids = [sc.virtual_ip_id for sc in story_characters]
        valid_vips = (
            self.db.query(VirtualIP.id)
            .filter(
                VirtualIP.id.in_(virtual_ip_ids),
                VirtualIP.is_deleted.is_(False),
            )
            .all()
        )
        valid_vip_ids = {v.id for v in valid_vips}
        invalid_refs = [
            sc.virtual_ip_id
            for sc in story_characters
            if sc.virtual_ip_id not in valid_vip_ids
        ]

        all_valid = len(invalid_refs) == 0
        checks.append(
            ReadinessCheck(
                name="main_characters_valid",
                passed=all_valid,
                severity="ERROR",
                message=(
                    "All character references are valid"
                    if all_valid
                    else f"{len(invalid_refs)} character(s) reference missing VirtualIPs"
                ),
                suggestion=(
                    None
                    if all_valid
                    else "Remove or update characters with invalid VirtualIP references"
                ),
            )
        )

        # Check if linked VirtualIPs have at least one approved image (ERROR)
        vips_with_images = self._check_vip_portraits(valid_vip_ids)
        vips_without_images = valid_vip_ids - vips_with_images
        all_have_portraits = len(vips_without_images) == 0

        checks.append(
            ReadinessCheck(
                name="virtual_ip_has_portrait",
                passed=all_have_portraits,
                severity="ERROR",
                message=(
                    "All characters have portrait images"
                    if all_have_portraits
                    else f"{len(vips_without_images)} character(s) missing portrait images"
                ),
                suggestion=(
                    None
                    if all_have_portraits
                    else "Generate or upload images for characters without portraits"
                ),
            )
        )

        return checks

    def _check_vip_portraits(self, vip_ids: set[int]) -> set[int]:
        """Return VIP IDs that have at least one image."""
        if not vip_ids:
            return set()

        images = (
            self.db.query(VirtualIPImage.virtual_ip_id)
            .filter(
                VirtualIPImage.virtual_ip_id.in_(vip_ids),
                VirtualIPImage.is_deleted.is_(False),
            )
            .distinct()
            .all()
        )
        return {img.virtual_ip_id for img in images}

    def _check_marketing_meta(self, story: Story) -> list[ReadinessCheck]:
        """Check marketing metadata for short_drama format (WARNING)."""
        checks = []

        # Only apply marketing checks to short_drama format
        if story.story_format != "short_drama":
            return checks

        extra = story.extra_metadata if isinstance(story.extra_metadata, dict) else {}

        # Market region check
        market_region = extra.get("market_region")
        has_market_region = bool(market_region)
        checks.append(
            ReadinessCheck(
                name="market_region_set",
                passed=has_market_region,
                severity="WARNING",
                message=(
                    f"Market region: {market_region}"
                    if has_market_region
                    else "Market region not set"
                ),
                suggestion=(
                    None
                    if has_market_region
                    else "Set market_region for better localization"
                ),
            )
        )

        # Micro genre check
        micro_genre = extra.get("micro_genre")
        has_micro_genre = bool(micro_genre)
        checks.append(
            ReadinessCheck(
                name="micro_genre_set",
                passed=has_micro_genre,
                severity="WARNING",
                message=(
                    f"Micro genre: {micro_genre}"
                    if has_micro_genre
                    else "Micro genre not set"
                ),
                suggestion=(
                    None
                    if has_micro_genre
                    else "Set micro_genre for targeted content generation"
                ),
            )
        )

        # Hook plan (optional but recommended)
        hook_plan = extra.get("hook_plan")
        has_hook_plan = bool(hook_plan)
        checks.append(
            ReadinessCheck(
                name="hook_plan_present",
                passed=has_hook_plan,
                severity="INFO",
                message=(
                    "Hook plan defined"
                    if has_hook_plan
                    else "No hook plan defined"
                ),
                suggestion=(
                    None
                    if has_hook_plan
                    else "Consider adding a hook_plan for engagement optimization"
                ),
            )
        )

        return checks

    def _check_content_quality(self, story: Story) -> list[ReadinessCheck]:
        """Check content quality fields (ERROR and WARNING)."""
        checks = []

        # Synopsis check (ERROR - strongly recommended)
        synopsis = story.synopsis or ""
        has_synopsis = len(synopsis.strip()) >= 50
        checks.append(
            ReadinessCheck(
                name="synopsis_present",
                passed=has_synopsis,
                severity="ERROR",
                message=(
                    f"Synopsis has {len(synopsis)} characters"
                    if has_synopsis
                    else "Synopsis missing or too short (< 50 chars)"
                ),
                suggestion=(
                    None
                    if has_synopsis
                    else "Add a detailed synopsis (at least 50 characters)"
                ),
            )
        )

        # Main conflict (WARNING)
        main_conflict = story.main_conflict or ""
        has_conflict = bool(main_conflict.strip())
        checks.append(
            ReadinessCheck(
                name="main_conflict_present",
                passed=has_conflict,
                severity="WARNING",
                message=(
                    "Main conflict defined"
                    if has_conflict
                    else "Main conflict not defined"
                ),
                suggestion=(
                    None
                    if has_conflict
                    else "Define the main conflict for better story structure"
                ),
            )
        )

        # Setting (WARNING - at least one of time/location)
        has_time = bool(story.setting_time and story.setting_time.strip())
        has_location = bool(story.setting_location and story.setting_location.strip())
        has_setting = has_time or has_location
        checks.append(
            ReadinessCheck(
                name="setting_present",
                passed=has_setting,
                severity="WARNING",
                message=(
                    "Setting defined"
                    if has_setting
                    else "Neither time nor location setting defined"
                ),
                suggestion=(
                    None
                    if has_setting
                    else "Add setting_time or setting_location for context"
                ),
            )
        )

        return checks

    def _check_optional_content(self, story: Story) -> list[ReadinessCheck]:
        """Check optional content fields (INFO)."""
        checks = []

        # World building (INFO)
        has_world_building = bool(story.world_building and story.world_building.strip())
        checks.append(
            ReadinessCheck(
                name="world_building_present",
                passed=has_world_building,
                severity="INFO",
                message=(
                    "World building defined"
                    if has_world_building
                    else "No world building details"
                ),
                suggestion=(
                    None
                    if has_world_building
                    else "Consider adding world_building for richer context"
                ),
            )
        )

        # Character relationships validation (INFO)
        relationships = story.character_relationships
        if relationships is not None:
            is_valid = self._validate_json_field(relationships)
            checks.append(
                ReadinessCheck(
                    name="character_relationships_valid",
                    passed=is_valid,
                    severity="INFO",
                    message=(
                        "Character relationships are well-formed"
                        if is_valid
                        else "Character relationships JSON may be malformed"
                    ),
                    suggestion=(
                        None
                        if is_valid
                        else "Review character_relationships JSON structure"
                    ),
                )
            )

        return checks

    def _validate_json_field(self, value) -> bool:
        """Validate that a JSON field is well-formed."""
        if value is None:
            return True
        if isinstance(value, (dict, list)):
            return True
        if isinstance(value, str):
            try:
                json.loads(value)
                return True
            except (json.JSONDecodeError, TypeError):
                return False
        return False

    def _build_summary(
        self, checks: list[ReadinessCheck], ready: bool, can_proceed: bool
    ) -> str:
        """Build human-readable summary."""
        failed = [c for c in checks if not c.passed]
        if not failed:
            return "All readiness checks passed"

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

        status = "Ready" if ready else ("Can proceed with caution" if can_proceed else "Not ready")
        return f"{status}: {', '.join(parts)}"
