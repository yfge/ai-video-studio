"""Processor for persisted Timeline grid storyboard sheet tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.models.task import TaskStatus
from app.models.timeline import MediaAsset
from app.prompts.template_audit import sha256_text
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import MediaAssetRepository, TimelineRepository
from app.services.ai_service import ai_service
from app.services.storyboard.grid_storyboard_sheet_spec import (
    apply_grid_storyboard_sheet_to_spec,
)
from app.services.storyboard.storyboard_image_generation import (
    generate_storyboard_image_urls,
)
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_revision_service import TimelineRevisionService
from app.services.timeline_spec_validation import validate_timeline_spec
from sqlalchemy.orm import Session

ImageGenerator = Callable[..., Awaitable[dict[str, Any]]]
ImagePersister = Callable[..., Awaitable[dict[str, Any]]]


class GridStoryboardSheetProcessor:
    def __init__(
        self,
        db: Session,
        *,
        image_generator: ImageGenerator | None = None,
        image_persister: ImagePersister | None = None,
    ):
        self.db = db
        self.timelines = TimelineRepository(db)
        self.media_assets = MediaAssetRepository(db)
        self.tasks = TaskRepository(db)
        self.revisions = TimelineRevisionService(db)
        self.clip_lineage = TimelineClipAssetLineageService(db)
        self.image_generator = image_generator or generate_storyboard_image_urls
        self.image_persister = image_persister or ai_service._persist_generated_image

    async def process_grid_sheet_task(
        self,
        task_id: int,
        payload: dict[str, Any],
        user_id: int | None,
    ) -> None:
        task = self.tasks.get_by_id(task_id)
        if task is None:
            raise RuntimeError("grid_storyboard_task_not_found")
        try:
            task.status = TaskStatus.PROCESSING
            task.error_message = None
            self.db.commit()
            await self._process(task, payload, user_id)
            task.status = TaskStatus.COMPLETED
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            task = self.tasks.get_by_id(task_id)
            if task is not None:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc)
                self.db.commit()
            raise

    async def _process(self, task, payload: dict[str, Any], user_id: int | None) -> None:
        timeline_id = _maybe_int(payload.get("timeline_id"))
        expected_version = _maybe_int(payload.get("expected_version"))
        if not timeline_id or not expected_version:
            raise RuntimeError("grid_storyboard_payload_invalid")

        timeline = self.timelines.get_by_id(timeline_id)
        if timeline is None or timeline.is_deleted:
            raise RuntimeError("timeline_not_found")
        if timeline.version != expected_version:
            raise RuntimeError("timeline version conflict")

        result = await self.image_generator(
            prompt=payload.get("sheet_prompt") or "",
            refs=payload.get("reference_images") or [],
            model=payload.get("model"),
            generation_profile=payload.get("generation_profile"),
            count=1,
            size=payload.get("size"),
            aspect_ratio=payload.get("aspect_ratio"),
            width=payload.get("width"),
            height=payload.get("height"),
            style=payload.get("style"),
            style_preset_id=None,
            style_spec=None,
            seed=None,
            steps=None,
            cfg_scale=None,
            negative_prompt=None,
            strength=None,
            ai_service=ai_service,
        )
        urls = result.get("urls") if isinstance(result, dict) else None
        if not urls:
            raise RuntimeError("grid_storyboard_generation_returned_no_images")

        source_version = timeline.version
        media_asset = await self._persist_sheet_asset(
            source_url=str(urls[0]),
            result=result,
            payload=payload,
            task_id=task.id,
            timeline_id=timeline.id,
            timeline_version=source_version,
            user_id=user_id,
        )
        next_version = timeline.version + 1
        updated_spec = apply_grid_storyboard_sheet_to_spec(
            timeline.spec if isinstance(timeline.spec, dict) else {},
            panels=payload.get("panels") or [],
            sheet_media_asset=media_asset,
            panel_count=_maybe_int(payload.get("panel_count")) or 0,
            columns=_maybe_int(payload.get("columns")) or 0,
            rows=_maybe_int(payload.get("rows")) or 0,
            prompt_sha256=sha256_text(payload.get("sheet_prompt") or ""),
            source_timeline_version=source_version,
            generated_at=_utc_now(),
        )
        self._apply_updated_spec(timeline, updated_spec, next_version, user_id)

    async def _persist_sheet_asset(
        self,
        *,
        source_url: str,
        result: dict[str, Any],
        payload: dict[str, Any],
        task_id: int,
        timeline_id: int,
        timeline_version: int,
        user_id: int | None,
    ) -> MediaAsset:
        stored = await self.image_persister(
            image_data=source_url,
            ip_name=f"timeline-{timeline_id}",
            category="storyboard-grid",
            prefix="ai-generated/storyboard-grid",
            metadata={
                "task_id": task_id,
                "timeline_id": timeline_id,
                "timeline_version": timeline_version,
                "kind": "timeline_storyboard_grid",
            },
            require_upload=False,
        )
        file_url = _string_value(stored.get("oss_url")) or source_url
        file_path = _string_value(stored.get("relative_path")) or _string_value(
            stored.get("local_file_path")
        )
        existing = self.media_assets.find_by_location(
            asset_type="image",
            file_url=file_url,
            file_path=file_path,
        )
        if existing is not None:
            return existing
        asset = self.media_assets.create(
            asset_type="image",
            origin="generated",
            file_url=file_url,
            file_path=file_path,
            mime_type="image/png",
            extra_metadata=_sheet_metadata(result, payload, task_id),
            created_by=user_id,
        )
        self.db.flush()
        return asset

    def _apply_updated_spec(self, timeline, spec, next_version, user_id) -> None:
        spec["version"] = next_version
        spec["timeline_id"] = timeline.id
        validate_timeline_spec(
            spec,
            episode_id=timeline.episode_id,
            script_id=timeline.script_id,
            timeline_id=timeline.id,
            expected_version=next_version,
            require_timeline_id=True,
        )
        self.revisions.ensure_revision(
            timeline,
            reason="pre_grid_storyboard_snapshot",
            user_id=user_id,
        )
        timeline.spec = spec
        timeline.version = next_version
        timeline.updated_by = user_id
        timeline.rollback_of_version = None
        timeline.rollback_target_version = None
        timeline.rolled_back_at = None
        timeline.rolled_back_by = None
        timeline.spec = self.revisions.spec_with_identity(timeline)
        self.clip_lineage.sync_timeline_assets(timeline, user_id=user_id)
        self.revisions.ensure_revision(
            timeline,
            reason="grid_storyboard_generated",
            user_id=user_id,
        )


def _sheet_metadata(
    result: dict[str, Any],
    payload: dict[str, Any],
    task_id: int,
) -> dict[str, Any]:
    return {
        "kind": "timeline_storyboard_grid",
        "task_id": task_id,
        "timeline_id": payload.get("timeline_id"),
        "timeline_version": payload.get("timeline_version"),
        "provider": result.get("provider"),
        "model": result.get("model") or payload.get("model"),
        "image_gen": result.get("image_gen"),
        "panel_count": payload.get("panel_count"),
        "columns": payload.get("columns"),
        "rows": payload.get("rows"),
    }


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
