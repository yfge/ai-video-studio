#!/usr/bin/env python3
"""
Backfill legacy Task.task_type values.

Context:
- Older async generation endpoints stored many non-image tasks using the fallback
  task_type=IMAGE_GENERATION. After TaskType was expanded, those historical rows
  should be corrected to the right domain type so /tasks filtering is meaningful.

This script updates tasks where task_type is IMAGE_GENERATION and the title/prompt
matches a known pattern (story/episode/script/dialogue_audio/timeline/storyboard/video/text).

Safe defaults:
- Dry-run by default (prints counts and samples).
- Requires --apply to perform updates.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy import not_, or_
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.task import Task, TaskType  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backfill_task_types")


def _parse_iso_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.replace(tzinfo=None)


@dataclass(frozen=True)
class BackfillRule:
    label: str
    target: TaskType
    condition: object


def _rules() -> list[BackfillRule]:
    return [
        BackfillRule(
            label="story_generation",
            target=TaskType.STORY_GENERATION,
            condition=or_(
                Task.title.like("生成故事%"),
                Task.prompt.like("Story outline:%"),
                Task.description.like("%故事生成%"),
            ),
        ),
        BackfillRule(
            label="episode_generation",
            target=TaskType.EPISODE_GENERATION,
            condition=or_(
                Task.title.like("生成剧集%"),
                Task.title.like("重新生成剧集%"),
                Task.prompt.like("Episode plan for story %"),
                Task.prompt.like("Regenerate episode %"),
            ),
        ),
        BackfillRule(
            label="script_generation",
            target=TaskType.SCRIPT_GENERATION,
            condition=or_(
                Task.title.like("生成剧本%"),
                Task.title.like("剧本重新生成%"),
                Task.prompt.like("Script for episode %"),
                Task.prompt.like("Script regeneration for script %"),
            ),
        ),
        BackfillRule(
            label="text_generation",
            target=TaskType.TEXT_GENERATION,
            condition=or_(
                Task.title.like("导出知乎体小说%"),
                Task.prompt.like("Zhihu novel export:%"),
            ),
        ),
        BackfillRule(
            label="dialogue_audio_generation",
            target=TaskType.DIALOGUE_AUDIO_GENERATION,
            condition=or_(
                Task.title.like("对白音轨生成%"),
                Task.prompt.like("Dialogue audio generation for script %"),
            ),
        ),
        BackfillRule(
            label="timeline_generation",
            target=TaskType.TIMELINE_GENERATION,
            condition=or_(
                Task.title.like("时间轴生成%"),
                Task.prompt.like("Episode audio timeline generation for script %"),
            ),
        ),
        BackfillRule(
            label="timeline_pipeline",
            target=TaskType.TIMELINE_PIPELINE,
            condition=or_(
                Task.title.like("一键时间轴流水线%"),
                Task.prompt.like("Timeline pipeline for script %"),
            ),
        ),
        BackfillRule(
            label="storyboard_generation",
            target=TaskType.STORYBOARD_GENERATION,
            condition=or_(
                Task.title.like("分镜生成%"),
                Task.title.like("分镜占位生成%"),
                Task.prompt.like("Storyboard generation for script %"),
                Task.prompt.like(
                    "Storyboard placeholder generation from audio timeline for script %"
                ),
            ),
        ),
        BackfillRule(
            label="storyboard_image_generation",
            target=TaskType.STORYBOARD_IMAGE_GENERATION,
            condition=or_(
                Task.title.like("分镜图像生成%"),
                Task.prompt.like("Storyboard image generation for script %"),
            ),
        ),
        BackfillRule(
            label="virtual_ip_image_generation",
            target=TaskType.VIRTUAL_IP_IMAGE_GENERATION,
            condition=or_(
                Task.title.like("虚拟IP文生图%"),
                Task.prompt.like("VirtualIP image gen for %"),
                Task.prompt.like('为虚拟IP "%'),
                Task.prompt.like("为虚拟IP %生成%图像%"),
            ),
        ),
        BackfillRule(
            label="virtual_ip_image_variant_generation",
            target=TaskType.VIRTUAL_IP_IMAGE_VARIANT_GENERATION,
            condition=or_(
                Task.title.like("虚拟IP图生图%"),
                Task.prompt.like("VirtualIP img2img for image %"),
            ),
        ),
        BackfillRule(
            label="environment_image_generation",
            target=TaskType.ENVIRONMENT_IMAGE_GENERATION,
            condition=or_(
                Task.title.like("环境文生图%"),
            ),
        ),
        BackfillRule(
            label="environment_image_variant_generation",
            target=TaskType.ENVIRONMENT_IMAGE_VARIANT_GENERATION,
            condition=or_(
                Task.title.like("环境图生图%"),
            ),
        ),
        BackfillRule(
            label="video_generation",
            target=TaskType.VIDEO_GENERATION,
            condition=or_(
                Task.title.like("分镜视频生成%"),
                Task.prompt.like("Storyboard video generation for script %"),
            ),
        ),
    ]


def _base_query(
    session: Session,
    *,
    user_id: int | None,
    created_after: datetime | None,
    created_before: datetime | None,
):
    query = (
        session.query(Task)
        .filter(Task.is_deleted.is_(False))
        .filter(Task.task_type == TaskType.IMAGE_GENERATION)
    )
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    if created_after is not None:
        query = query.filter(Task.created_at >= created_after)
    if created_before is not None:
        query = query.filter(Task.created_at < created_before)
    return query


def _print_samples(tasks: Iterable[Task], *, header: str) -> None:
    logger.info(header)
    for task in tasks:
        logger.info("  - id=%s title=%s prompt=%s", task.id, task.title, task.prompt)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill legacy Task.task_type values"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply updates (default: dry-run)"
    )
    parser.add_argument(
        "--user-id", type=int, default=None, help="Only update tasks for user_id"
    )
    parser.add_argument(
        "--after",
        type=str,
        default=None,
        help="Only update tasks created at/after this ISO time (e.g. 2026-01-01T00:00:00Z)",
    )
    parser.add_argument(
        "--before",
        type=str,
        default=None,
        help="Only update tasks created before this ISO time (e.g. 2026-02-01T00:00:00Z)",
    )
    parser.add_argument(
        "--show-unmatched",
        type=int,
        default=10,
        help="Print N unmatched IMAGE_GENERATION samples (0 to disable)",
    )
    args = parser.parse_args()

    created_after = _parse_iso_datetime(args.after) if args.after else None
    created_before = _parse_iso_datetime(args.before) if args.before else None

    session = SessionLocal()
    try:
        base = _base_query(
            session,
            user_id=args.user_id,
            created_after=created_after,
            created_before=created_before,
        )
        total_candidates = base.count()
        logger.info("Candidates (task_type=IMAGE_GENERATION): %s", total_candidates)
        if total_candidates == 0:
            return 0

        rules = _rules()
        for rule in rules:
            matched = base.filter(rule.condition)
            count = matched.count()
            if count == 0:
                continue
            if args.apply:
                updated = matched.update(
                    {Task.task_type: rule.target}, synchronize_session=False
                )
                session.commit()
                logger.info(
                    "Updated %s -> %s: %s", rule.label, rule.target.value, updated
                )
            else:
                logger.info(
                    "Would update %s -> %s: %s", rule.label, rule.target.value, count
                )

        remaining = base.count()
        logger.info("Remaining IMAGE_GENERATION candidates: %s", remaining)

        if args.show_unmatched and remaining:
            all_conditions = or_(*[rule.condition for rule in rules])
            unmatched = (
                base.filter(not_(all_conditions))
                .order_by(Task.id.desc())
                .limit(int(args.show_unmatched))
                .all()
            )
            _print_samples(
                unmatched, header="Unmatched samples (still IMAGE_GENERATION):"
            )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
