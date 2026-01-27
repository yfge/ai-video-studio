#!/usr/bin/env python3
"""
Backfill Task.parameters.agent_run for historical tasks.

Context:
- New task executions persist a compact audit trail into Task.parameters.agent_run.
- Historical tasks (especially FAILED/CANCELLED) may be missing agent_run, which hurts
  auditability on /tasks.

This script targets terminal tasks whose parameters.agent_run is missing/empty and
writes a best-effort agent_run entry. For FAILED/CANCELLED tasks, it will also include
error context (Task.error_message) so the audit trail is closed.

Safe defaults:
- Dry-run by default (prints counts and samples).
- Requires --apply to perform updates.
- Supports user/time filtering for batch execution in production.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy.orm import Session


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.task import Task, TaskStatus, TaskType  # noqa: E402
from app.services.task_agent_run.utils import loads_task_parameters  # noqa: E402
from app.services.task_agent_run_persistence import persist_task_agent_run  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backfill_task_agent_runs")


TASK_TYPE_TO_KIND: dict[TaskType, str] = {
    TaskType.STORY_GENERATION: "story",
    TaskType.EPISODE_GENERATION: "episode",
    TaskType.SCRIPT_GENERATION: "script",
    TaskType.DIALOGUE_AUDIO_GENERATION: "dialogue_audio",
    TaskType.TIMELINE_GENERATION: "timeline_generation",
    TaskType.TIMELINE_PIPELINE: "timeline_pipeline",
    TaskType.STORYBOARD_GENERATION: "storyboard_generation",
    TaskType.STORYBOARD_IMAGE_GENERATION: "storyboard_images",
    TaskType.ENVIRONMENT_IMAGE_GENERATION: "environment_images",
    TaskType.ENVIRONMENT_IMAGE_VARIANT_GENERATION: "environment_image_variants",
    TaskType.VIRTUAL_IP_IMAGE_GENERATION: "virtual_ip_image",
    TaskType.VIRTUAL_IP_IMAGE_VARIANT_GENERATION: "virtual_ip_image_variants",
    TaskType.TEXT_GENERATION: "text_generation",
    TaskType.VIDEO_GENERATION: "video_generation",
}


def _parse_iso_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.replace(tzinfo=None)


def _parse_statuses(values: Optional[list[str]]) -> Optional[list[TaskStatus]]:
    if not values:
        return None
    result: list[TaskStatus] = []
    for raw in values:
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            result.append(TaskStatus(token))
    return result


def _parse_task_types(values: Optional[list[str]]) -> Optional[list[TaskType]]:
    if not values:
        return None
    result: list[TaskType] = []
    for raw in values:
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            result.append(TaskType(token))
    return result


def _base_query(
    session: Session,
    *,
    user_id: int | None,
    created_after: datetime | None,
    created_before: datetime | None,
    min_id: int | None,
    max_id: int | None,
    statuses: Optional[list[TaskStatus]],
    task_types: Optional[list[TaskType]],
):
    query = session.query(Task).filter(Task.is_deleted.is_(False))
    if min_id is not None:
        query = query.filter(Task.id >= min_id)
    if max_id is not None:
        query = query.filter(Task.id <= max_id)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    if created_after is not None:
        query = query.filter(Task.created_at >= created_after)
    if created_before is not None:
        query = query.filter(Task.created_at < created_before)
    if statuses:
        query = query.filter(Task.status.in_(statuses))
    if task_types:
        query = query.filter(Task.task_type.in_(task_types))
    return query.order_by(Task.id.asc())


def _has_agent_run(task: Task) -> bool:
    params = loads_task_parameters(getattr(task, "parameters", None))
    agent_run = params.get("agent_run")
    return bool(agent_run)


def _print_samples(tasks: Iterable[Task], *, header: str, limit: int) -> None:
    logger.info(header)
    for idx, task in enumerate(tasks):
        if idx >= limit:
            break
        logger.info(
            "  - id=%s type=%s status=%s title=%s",
            task.id,
            getattr(task.task_type, "value", task.task_type),
            getattr(task.status, "value", task.status),
            task.title,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill Task.parameters.agent_run for historical tasks"
    )
    parser.add_argument("--apply", action="store_true", help="Apply updates (default: dry-run)")
    parser.add_argument("--user-id", type=int, default=None, help="Only update tasks for user_id")
    parser.add_argument("--min-id", type=int, default=None, help="Only include tasks with id >= min_id")
    parser.add_argument("--max-id", type=int, default=None, help="Only include tasks with id <= max_id")
    parser.add_argument(
        "--after",
        type=str,
        default=None,
        help="Only include tasks created at/after this ISO time (e.g. 2026-01-01T00:00:00Z)",
    )
    parser.add_argument(
        "--before",
        type=str,
        default=None,
        help="Only include tasks created before this ISO time (e.g. 2026-02-01T00:00:00Z)",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=None,
        help="Only include status (comma-separated; default: completed,failed,cancelled)",
    )
    parser.add_argument(
        "--task-type",
        action="append",
        default=None,
        help="Only include task_type (comma-separated; default: mapped types only)",
    )
    parser.add_argument(
        "--max-updates",
        type=int,
        default=500,
        help="Max number of updates to apply in this run (default: 500)",
    )
    parser.add_argument(
        "--show-samples",
        type=int,
        default=10,
        help="Print N candidate samples in dry-run (0 to disable)",
    )
    args = parser.parse_args()

    created_after = _parse_iso_datetime(args.after) if args.after else None
    created_before = _parse_iso_datetime(args.before) if args.before else None

    statuses = _parse_statuses(args.status) if args.status else None
    if statuses is None:
        statuses = [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]

    task_types = _parse_task_types(args.task_type) if args.task_type else None
    if task_types is None:
        task_types = sorted(TASK_TYPE_TO_KIND.keys(), key=lambda t: t.value)

    session = SessionLocal()
    try:
        query = _base_query(
            session,
            user_id=args.user_id,
            created_after=created_after,
            created_before=created_before,
            min_id=args.min_id,
            max_id=args.max_id,
            statuses=statuses,
            task_types=task_types,
        )
        tasks = query.all()

        counters = Counter()
        candidates: list[Task] = []
        unmapped: list[Task] = []
        for task in tasks:
            counters["scanned"] += 1
            if _has_agent_run(task):
                counters["already_has_agent_run"] += 1
                continue
            kind = TASK_TYPE_TO_KIND.get(task.task_type)
            if not kind:
                counters["unmapped_task_type"] += 1
                unmapped.append(task)
                continue
            candidates.append(task)
            counters[f"candidate_status:{task.status.value}"] += 1
            counters[f"candidate_type:{task.task_type.value}"] += 1

        logger.info(
            "Scanned=%s candidates=%s already_has_agent_run=%s unmapped=%s",
            counters["scanned"],
            len(candidates),
            counters["already_has_agent_run"],
            len(unmapped),
        )

        if not args.apply:
            if args.show_samples:
                _print_samples(candidates, header="Candidate samples:", limit=args.show_samples)
                if unmapped:
                    _print_samples(
                        unmapped, header="Unmapped task_type samples:", limit=args.show_samples
                    )
            return 0

        applied = 0
        for task in candidates:
            if applied >= args.max_updates:
                logger.info("Reached --max-updates=%s; stopping.", args.max_updates)
                break
            kind = TASK_TYPE_TO_KIND.get(task.task_type)
            if not kind:
                continue
            request_dict = loads_task_parameters(getattr(task, "parameters", None))
            persist_task_agent_run(
                task_id=task.id,
                user_id=task.user_id,
                kind=kind,
                request_dict=request_dict,
                db_session=session,
            )
            applied += 1
            if applied % 50 == 0:
                logger.info("Applied %s updates...", applied)

        logger.info("Done. Applied %s updates.", applied)
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
