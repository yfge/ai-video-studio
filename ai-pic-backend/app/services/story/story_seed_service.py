"""Story Seed normalization, local editing, and downstream invalidation."""

import hashlib
import json
import re
import unicodedata
from datetime import datetime

from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryGenerationRequest
from app.schemas.story_seed import StorySeedModel
from fastapi import HTTPException

from .story_seed_thread_contract import (
    outline_has_open_threads,
    validate_seed_thread_contract,
)


def ending_is_covered(ending: str, contract: str) -> bool:
    normalized_ending = "".join(
        re.findall(
            r"[0-9a-z\u3400-\u9fff]+",
            unicodedata.normalize("NFKC", ending).casefold(),
        )
    )
    normalized_contract = "".join(
        re.findall(
            r"[0-9a-z\u3400-\u9fff]+",
            unicodedata.normalize("NFKC", contract).casefold(),
        )
    )
    if normalized_ending in normalized_contract:
        return True
    keywords = {
        normalized_ending[index : index + 2]
        for index in range(len(normalized_ending) - 1)
    }
    if not keywords:
        return False
    matched = keywords.intersection(
        normalized_contract[index : index + 2]
        for index in range(len(normalized_contract) - 1)
    )
    return len(matched) >= 3 and len(matched) / len(keywords) >= 0.2


def ensure_confirmable_seed(seed: StorySeedModel) -> None:
    if seed.schema_version != "story_seed_v2" or not seed.structured_outline:
        raise HTTPException(status_code=409, detail="只能确认 story_seed_v2 结构化大纲")
    if seed.structured_outline.status not in {"confirmed", "frozen"}:
        raise HTTPException(status_code=409, detail="结构化大纲尚未确认")
    try:
        validate_seed_thread_contract(
            seed.structured_outline,
            require_version=outline_has_open_threads(seed.structured_outline),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    ending = (seed.ending_direction or "").strip()
    last = seed.structured_outline.chapters[-1]
    ending_contract = "\n".join(
        [last.title, last.goal, *last.key_events, last.end_state]
    )
    if ending and not ending_is_covered(ending, ending_contract):
        raise HTTPException(
            status_code=409, detail="结局章节未覆盖 StorySeed ending_direction"
        )


def seed_from_generation(
    ai_content: dict,
    request: StoryGenerationRequest,
    characters: list[dict],
) -> StorySeedModel:
    if isinstance(ai_content.get("story_seed"), dict):
        return StorySeedModel.model_validate(ai_content["story_seed"])
    protagonists = [
        {
            "virtual_ip_business_id": item["business_id"],
            "initial_state": item.get("description")
            or item.get("background_story")
            or "故事开始时保持其基础角色设定",
        }
        for item in characters
    ]
    constraints = [request.world_building] if request.world_building else []
    return StorySeedModel(
        title=request.title,
        premise=ai_content.get("premise")
        or request.additional_requirements
        or request.title,
        outline=ai_content.get("synopsis")
        or ai_content.get("premise")
        or request.title,
        protagonists=protagonists,
        world_constraints=constraints,
        central_conflict=ai_content.get("main_conflict") or "核心目标受到结构性阻力",
        ending_direction=ai_content.get("resolution"),
        target_audience=request.target_audience,
        content_constraints=request.content_restrictions or [],
    )


class StorySeedService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def apply_local_update(
        self,
        story: Story,
        seed: StorySeedModel | dict,
        *,
        requested_status: str | None = None,
        expected_version: int | None = None,
        allow_task_id: int | None = None,
    ) -> None:
        seed = StorySeedModel.model_validate(seed)
        if expected_version is not None and int(story.story_seed_version or 1) != int(
            expected_version
        ):
            raise HTTPException(
                status_code=409, detail="StorySeed 版本已变化，请刷新后重试"
            )
        novel_repo = StoryNovelRepository(self.repo.session)
        revisions = novel_repo.story_revisions(story.id)
        active = novel_repo.active_task_for_targets(
            [story.business_id, *(item.business_id for item in revisions)],
            exclude_task_id=allow_task_id,
        )
        if active:
            raise HTTPException(
                status_code=409,
                detail=f"小说任务 {active.id} 正在运行，请先取消任务再修改 StorySeed",
            )
        if requested_status == "confirmed" and seed.schema_version == "story_seed_v2":
            ensure_confirmable_seed(seed)
            seed = seed.model_copy(
                update={
                    "structured_outline": seed.structured_outline.model_copy(
                        update={"status": "frozen"}
                    )
                }
            )
        before_hash = self._hash(story.story_seed)
        data = seed.model_dump(by_alias=True)
        after_hash = self._hash(data)
        changed = before_hash != after_hash
        story.story_seed = data
        story.story_seed_schema = seed.schema_version
        story.story_seed_status = requested_status or story.story_seed_status or "draft"
        story.story_seed_updated_at = datetime.utcnow()
        story.title = seed.title
        story.premise = seed.premise
        story.synopsis = seed.outline_text or seed.outline
        story.main_conflict = seed.central_conflict
        story.resolution = seed.ending_direction
        story.target_audience = seed.target_audience
        if changed:
            story.story_seed_version = int(story.story_seed_version or 0) + 1
            self._mark_downstream_review(story, before_hash, after_hash)

    def _mark_downstream_review(
        self, story: Story, before_hash: str | None, after_hash: str
    ) -> None:
        metadata = dict(story.extra_metadata or {})
        metadata["story_seed_downstream"] = {
            "status": "review_required",
            "source_before_hash": before_hash,
            "source_after_hash": after_hash,
            "detected_at": datetime.utcnow().isoformat(),
        }
        story.extra_metadata = metadata
        story.memory_review_status = "review_required"
        reason = {
            "reason_code": "story_seed_changed",
            **metadata["story_seed_downstream"],
        }
        for revision in StoryNovelRepository(self.repo.session).story_revisions(
            story.id
        ):
            revision.continuity_status = "review_required"
            if revision.adaptation_plan_status != "empty":
                revision.adaptation_plan_status = "stale"
            for chapter in revision.chapters or []:
                chapter.review_status = "review_required"
        for episode in self.repo.list_story_episodes(story.id):
            if episode.memory_snapshot_evidence:
                episode.memory_snapshot_stale = True
                episode.memory_snapshot_stale_reason = reason
        for script in self.repo.list_story_scripts(story.id):
            script_metadata = dict(script.extra_metadata or {})
            script_metadata["narrative_memory_stale"] = reason
            script.extra_metadata = script_metadata

    @staticmethod
    def _hash(value) -> str | None:
        if not value:
            return None
        raw = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(raw.encode()).hexdigest()
