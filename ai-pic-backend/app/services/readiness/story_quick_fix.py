"""
Story quick-fix service for auto-fixing readiness issues.

Automatically fills missing fields (synopsis, main_conflict, setting)
using AI generation based on existing story data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.models.script import Story
from app.schemas.readiness import (
    FixApplied,
    FixSkipped,
    QuickFixImprovement,
    QuickFixResponse,
    ReadinessCheck,
)
from app.services.readiness.story_readiness import StoryReadinessChecker

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger()

# Checks that can be auto-fixed
AUTO_FIXABLE_CHECKS = {
    "synopsis_present",
    "main_conflict_present",
    "setting_present",
    "world_building_present",
}


class StoryQuickFixService:
    """Auto-fixes missing story fields using AI generation."""

    def __init__(self, db: "Session"):
        self.db = db
        self.readiness_checker = StoryReadinessChecker(db)

    async def fix_story(
        self,
        story: Story,
        *,
        dry_run: bool = False,
    ) -> QuickFixResponse:
        """
        Analyze and fix missing story fields.

        Args:
            story: Story model instance
            dry_run: If True, only report what would be fixed without applying

        Returns:
            QuickFixResponse with fixes applied and updated readiness
        """
        # Run initial readiness check
        initial_result = self.readiness_checker.check(story)

        # Identify fixable issues
        fixable_issues = [
            c for c in initial_result.checks
            if not c.passed and c.name in AUTO_FIXABLE_CHECKS
        ]

        if not fixable_issues:
            return QuickFixResponse(
                story_id=story.id,
                dry_run=dry_run,
                fixes_applied=[],
                fixes_skipped=[],
                initial_readiness=initial_result,
                final_readiness=initial_result,
                improvement=QuickFixImprovement(
                    initial_failed=initial_result.failed_count,
                    final_failed=initial_result.failed_count,
                    fixed_count=0,
                ),
            )

        # Generate fixes
        fixes_applied: list[FixApplied] = []
        fixes_skipped: list[FixSkipped] = []

        for issue in fixable_issues:
            fix = await self._generate_fix(story, issue)
            if fix:
                if not dry_run:
                    self._apply_fix(story, fix)
                fixes_applied.append(fix)
            else:
                fixes_skipped.append(FixSkipped(
                    check_name=issue.name,
                    reason="Could not generate fix",
                ))

        # Commit changes if not dry run
        if not dry_run and fixes_applied:
            self.db.commit()
            self.db.refresh(story)

        # Run final readiness check
        final_result = self.readiness_checker.check(story)

        return QuickFixResponse(
            story_id=story.id,
            dry_run=dry_run,
            fixes_applied=fixes_applied,
            fixes_skipped=fixes_skipped,
            initial_readiness=initial_result,
            final_readiness=final_result,
            improvement=QuickFixImprovement(
                initial_failed=initial_result.failed_count,
                final_failed=final_result.failed_count,
                fixed_count=len(fixes_applied),
            ),
        )

    async def _generate_fix(
        self,
        story: Story,
        issue: ReadinessCheck,
    ) -> FixApplied | None:
        """Generate a fix for a specific issue."""
        try:
            if issue.name == "synopsis_present":
                return await self._fix_synopsis(story)
            elif issue.name == "main_conflict_present":
                return await self._fix_main_conflict(story)
            elif issue.name == "setting_present":
                return await self._fix_setting(story)
            elif issue.name == "world_building_present":
                return await self._fix_world_building(story)
        except Exception as e:
            logger.warning(f"Failed to generate fix for {issue.name}: {e}")
            return None
        return None

    async def _fix_synopsis(self, story: Story) -> FixApplied | None:
        """Generate synopsis from title/genre/premise."""
        context_parts = []
        if story.title:
            context_parts.append(f"标题：{story.title}")
        if story.genre:
            context_parts.append(f"类型：{story.genre}")
        if story.premise:
            context_parts.append(f"前提：{story.premise}")
        if story.theme:
            context_parts.append(f"主题：{story.theme}")

        if not context_parts:
            return None

        synopsis = await self._generate_text(
            f"根据以下信息，生成一段50-100字的故事概要（synopsis）：\n"
            f"{chr(10).join(context_parts)}\n\n"
            f"要求：简洁明了，概括故事主线和核心冲突。只输出概要内容，不要其他文字。"
        )

        if synopsis and len(synopsis.strip()) >= 50:
            return FixApplied(
                check_name="synopsis_present",
                field="synopsis",
                old_value=story.synopsis,
                new_value=synopsis.strip(),
            )
        return None

    async def _fix_main_conflict(self, story: Story) -> FixApplied | None:
        """Generate main_conflict from synopsis/premise."""
        context_parts = []
        if story.title:
            context_parts.append(f"标题：{story.title}")
        if story.genre:
            context_parts.append(f"类型：{story.genre}")
        if story.synopsis:
            context_parts.append(f"概要：{story.synopsis}")
        elif story.premise:
            context_parts.append(f"前提：{story.premise}")

        if not context_parts:
            return None

        conflict = await self._generate_text(
            f"根据以下信息，生成故事的主要冲突（main_conflict）描述：\n"
            f"{chr(10).join(context_parts)}\n\n"
            f"要求：一句话概括核心矛盾或冲突。只输出冲突描述，不要其他文字。"
        )

        if conflict and conflict.strip():
            return FixApplied(
                check_name="main_conflict_present",
                field="main_conflict",
                old_value=story.main_conflict,
                new_value=conflict.strip(),
            )
        return None

    async def _fix_setting(self, story: Story) -> FixApplied | None:
        """Generate setting_time from genre/synopsis."""
        context_parts = []
        if story.genre:
            context_parts.append(f"类型：{story.genre}")
        if story.synopsis:
            context_parts.append(f"概要：{story.synopsis}")
        elif story.premise:
            context_parts.append(f"前提：{story.premise}")

        if not context_parts:
            # Default setting based on genre
            return FixApplied(
                check_name="setting_present",
                field="setting_time",
                old_value=story.setting_time,
                new_value="当代",
            )

        setting = await self._generate_text(
            f"根据以下信息，生成故事的时间设定（setting_time）：\n"
            f"{chr(10).join(context_parts)}\n\n"
            f"要求：简短描述时间背景，如'当代'、'2024年'、'古代唐朝'等。"
            f"只输出时间设定，不要其他文字。"
        )

        if setting and setting.strip():
            return FixApplied(
                check_name="setting_present",
                field="setting_time",
                old_value=story.setting_time,
                new_value=setting.strip(),
            )
        return None

    async def _fix_world_building(self, story: Story) -> FixApplied | None:
        """Generate world_building from genre/setting/synopsis."""
        context_parts = []
        if story.genre:
            context_parts.append(f"类型：{story.genre}")
        if story.setting_time:
            context_parts.append(f"时间：{story.setting_time}")
        if story.setting_location:
            context_parts.append(f"地点：{story.setting_location}")
        if story.synopsis:
            context_parts.append(f"概要：{story.synopsis}")

        if not context_parts:
            return None

        world = await self._generate_text(
            f"根据以下信息，生成简短的世界观设定（world_building）：\n"
            f"{chr(10).join(context_parts)}\n\n"
            f"要求：2-3句话描述故事世界的基本规则和氛围。只输出世界观描述，不要其他文字。"
        )

        if world and world.strip():
            return FixApplied(
                check_name="world_building_present",
                field="world_building",
                old_value=story.world_building,
                new_value=world.strip(),
            )
        return None

    async def _generate_text(self, prompt: str) -> str | None:
        """Generate text using AI service."""
        try:
            from app.services.ai_service_manager import get_ai_manager

            manager = get_ai_manager()
            response = await manager.generate_text(
                prompt=prompt,
                prefer_provider="deepseek",
                max_tokens=200,
            )
            return response.content if response else None
        except Exception as e:
            logger.warning(f"AI generation failed: {e}")
            return None

    def _apply_fix(self, story: Story, fix: FixApplied) -> None:
        """Apply a fix to the story model."""
        setattr(story, fix.field, fix.new_value)
        new_val_preview = str(fix.new_value)[:50] if fix.new_value else ""
        logger.info(f"Applied fix for {fix.check_name}: {fix.field}={new_val_preview}...")
