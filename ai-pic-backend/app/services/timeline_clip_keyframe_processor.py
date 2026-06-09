"""Processor for Timeline clip start/end keyframe tasks."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.models.task import TaskStatus
from app.models.timeline import MediaAsset
from app.prompts.template_audit import sha256_text
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import (
    MediaAssetRepository,
    TimelineRepository,
)
from app.services.ai_service import ai_service
from app.services.storyboard.grid_storyboard_sheet_payload import (
    maybe_int,
    string_value,
    utc_now,
)
from app.services.storyboard.storyboard_image_generation import (
    generate_storyboard_image_urls,
)
from app.services.timeline_clip_asset_lineage import TimelineClipAssetLineageService
from app.services.timeline_clip_keyframe_payload import (
    keyframe_frames,
    keyframe_metadata,
)
from app.services.timeline_clip_keyframe_spec import apply_clip_keyframes_to_spec
from app.services.timeline_revision_service import TimelineRevisionService
from app.services.timeline_spec_validation import validate_timeline_spec
from sqlalchemy.orm import Session

ImageGenerator = Callable[..., Awaitable[dict[str, Any]]]
ImagePersister = Callable[..., Awaitable[dict[str, Any]]]


class TimelineClipKeyframeProcessor:
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

    async def process_keyframe_task(
        self,
        task_id: int,
        payload: dict[str, Any],
        user_id: int | None,
    ) -> None:
        task = self.tasks.get_by_id(task_id)
        if task is None:
            raise RuntimeError("timeline_clip_keyframe_task_not_found")
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

    async def _process(
        self, task, payload: dict[str, Any], user_id: int | None
    ) -> None:
        timeline_id = maybe_int(payload.get("timeline_id"))
        expected_version = maybe_int(payload.get("expected_version"))
        clip_id = string_value(payload.get("clip_id"))
        if not timeline_id or not expected_version or not clip_id:
            raise RuntimeError("timeline_clip_keyframe_payload_invalid")
        timeline = self._compatible_timeline_or_raise(timeline_id, expected_version)
        source_version = maybe_int(payload.get("timeline_version")) or expected_version

        frame_assets: dict[str, MediaAsset] = {}
        prompt_hashes: dict[str, str] = {}
        for frame in keyframe_frames(payload):
            result = await self._generate_frame(frame, payload)
            urls = result.get("urls") if isinstance(result, dict) else None
            if not urls:
                raise RuntimeError(
                    "timeline_clip_keyframe_generation_returned_no_images"
                )
            role = frame["role"]
            prompt_hashes[role] = sha256_text(frame["prompt"])
            frame_assets[role] = await self._persist_frame_asset(
                source_url=str(urls[0]),
                result=result,
                payload=payload,
                role=role,
                task_id=task.id,
                timeline_id=timeline_id,
                timeline_version=source_version,
                user_id=user_id,
            )

        timeline = self._compatible_timeline_or_raise(
            timeline_id,
            expected_version,
            for_update=True,
        )
        next_version = timeline.version + 1
        updated_spec = apply_clip_keyframes_to_spec(
            timeline.spec if isinstance(timeline.spec, dict) else {},
            clip_id=clip_id,
            frames=frame_assets,
            prompt_sha256_by_role=prompt_hashes,
            source_timeline_version=source_version,
            generated_at=utc_now(),
        )
        self._apply_updated_spec(timeline, updated_spec, next_version, user_id)

    async def _generate_frame(
        self,
        frame: dict[str, str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self.image_generator(
            prompt=frame["prompt"],
            refs=payload.get("reference_images") or [],
            model=payload.get("model"),
            generation_profile=payload.get("generation_profile"),
            count=1,
            size=payload.get("size"),
            aspect_ratio=payload.get("aspect_ratio"),
            width=payload.get("width"),
            height=payload.get("height"),
            style=None,
            style_preset_id=None,
            style_spec=None,
            seed=None,
            steps=None,
            cfg_scale=None,
            negative_prompt=None,
            strength=None,
            ai_service=ai_service,
        )

    async def _persist_frame_asset(
        self,
        *,
        source_url: str,
        result: dict[str, Any],
        payload: dict[str, Any],
        role: str,
        task_id: int,
        timeline_id: int,
        timeline_version: int,
        user_id: int | None,
    ) -> MediaAsset:
        stored = await self.image_persister(
            image_data=source_url,
            ip_name=f"timeline-{timeline_id}",
            category="clip-keyframes",
            prefix="ai-generated/clip-keyframes",
            metadata={
                "kind": "timeline_clip_keyframe",
                "role": role,
                "task_id": task_id,
                "timeline_id": timeline_id,
                "timeline_version": timeline_version,
                "clip_id": payload.get("clip_id"),
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
            extra_metadata=keyframe_metadata(result, payload, task_id, role),
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
            reason="pre_clip_keyframes_snapshot",
            user_id=user_id,
        )
        timeline.spec = spec
        timeline.version = next_version
        timeline.updated_by = user_id
        timeline.spec = self.revisions.spec_with_identity(timeline)
        self.clip_lineage.sync_timeline_assets(timeline, user_id=user_id)
        self.revisions.ensure_revision(
            timeline,
            reason="clip_keyframes_generated",
            user_id=user_id,
        )

    def _compatible_timeline_or_raise(
        self,
        timeline_id: int,
        expected_version: int,
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
        if timeline.version != expected_version:
            raise RuntimeError("timeline version conflict")
        return timeline
