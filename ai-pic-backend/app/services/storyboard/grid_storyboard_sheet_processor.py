"""Processor for persisted Timeline grid storyboard sheet tasks."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.models.task import TaskStatus
from app.models.timeline import MediaAsset
from app.prompts.template_audit import sha256_text
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import MediaAssetRepository, TimelineRepository
from app.services.ai_service import ai_service
from app.services.storyboard.grid_storyboard_sheet_payload import (
    grid_payload_matches_current_timeline,
    maybe_int,
    sheet_metadata,
    string_value,
    utc_now,
)
from app.services.storyboard.grid_storyboard_sheet_spec import (
    apply_clip_storyboard_sheet_to_spec,
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
        timeline_id = maybe_int(payload.get("timeline_id"))
        expected_version = maybe_int(payload.get("expected_version"))
        if not timeline_id or not expected_version:
            raise RuntimeError("grid_storyboard_payload_invalid")

        self._compatible_timeline_or_raise(timeline_id, payload)
        source_version = maybe_int(payload.get("timeline_version")) or expected_version

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

        media_asset = await self._persist_sheet_asset(
            source_url=str(urls[0]),
            result=result,
            payload=payload,
            task_id=task.id,
            timeline_id=timeline_id,
            timeline_version=source_version,
            user_id=user_id,
        )
        timeline = self._compatible_timeline_or_raise(
            timeline_id,
            payload,
            for_update=True,
        )
        next_version = timeline.version + 1
        updated_spec = self._updated_spec_with_sheet(
            timeline,
            payload,
            media_asset,
            source_version,
        )
        self._apply_updated_spec(timeline, updated_spec, next_version, user_id)

    def _updated_spec_with_sheet(
        self,
        timeline,
        payload: dict[str, Any],
        media_asset: MediaAsset,
        source_version: int,
    ) -> dict[str, Any]:
        common = {
            "panels": payload.get("panels") or [],
            "sheet_media_asset": media_asset,
            "panel_count": maybe_int(payload.get("panel_count")) or 0,
            "columns": maybe_int(payload.get("columns")) or 0,
            "rows": maybe_int(payload.get("rows")) or 0,
            "prompt_sha256": sha256_text(payload.get("sheet_prompt") or ""),
            "source_timeline_version": source_version,
            "generated_at": utc_now(),
        }
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        if payload.get("kind") == "timeline_clip_storyboard":
            clip_id = string_value(payload.get("clip_id"))
            if not clip_id:
                raise RuntimeError("clip_storyboard_payload_invalid")
            return apply_clip_storyboard_sheet_to_spec(
                spec,
                clip_id=clip_id,
                **common,
            )
        return apply_grid_storyboard_sheet_to_spec(spec, **common)

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
            category=(
                "clip-storyboard"
                if payload.get("kind") == "timeline_clip_storyboard"
                else "storyboard-grid"
            ),
            prefix=(
                "ai-generated/clip-storyboard"
                if payload.get("kind") == "timeline_clip_storyboard"
                else "ai-generated/storyboard-grid"
            ),
            metadata={
                "task_id": task_id,
                "timeline_id": timeline_id,
                "timeline_version": timeline_version,
                "clip_id": payload.get("clip_id"),
                "kind": payload.get("kind") or "timeline_storyboard_grid",
            },
            require_upload=False,
        )
        file_url = string_value(stored.get("oss_url")) or source_url
        file_path = string_value(stored.get("relative_path")) or string_value(
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
            extra_metadata=sheet_metadata(result, payload, task_id),
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
            reason=(
                "pre_clip_storyboard_snapshot"
                if _is_clip_storyboard_spec(spec)
                else "pre_grid_storyboard_snapshot"
            ),
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
            reason=(
                "clip_storyboard_generated"
                if _is_clip_storyboard_spec(spec)
                else "grid_storyboard_generated"
            ),
            user_id=user_id,
        )

    def _compatible_timeline_or_raise(
        self,
        timeline_id: int,
        payload: dict[str, Any],
        *,
        for_update: bool = False,
    ):
        timeline = (
            self.timelines.get_by_id_for_update(timeline_id)
            if for_update
            else self.timelines.get_by_id(timeline_id)
        )
        if timeline is None or timeline.is_deleted:
            raise RuntimeError("timeline_not_found")
        expected_version = maybe_int(payload.get("expected_version"))
        if expected_version is not None and timeline.version == expected_version:
            return timeline
        if not grid_payload_matches_current_timeline(timeline, payload):
            raise RuntimeError("timeline version conflict")
        return timeline


def _is_clip_storyboard_spec(spec: dict[str, Any]) -> bool:
    support_views = spec.get("support_views")
    return isinstance(support_views, dict) and isinstance(
        support_views.get("clip_storyboards"),
        dict,
    )
