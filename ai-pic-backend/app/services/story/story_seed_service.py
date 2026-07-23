"""Story Seed normalization, local editing, and downstream invalidation."""

import hashlib
import json
from datetime import datetime

from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.generation_requests import StoryGenerationRequest
from app.schemas.story_seed import StorySeedModel


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
        seed: StorySeedModel,
        *,
        requested_status: str | None = None,
    ) -> None:
        before_hash = self._hash(story.story_seed)
        data = seed.model_dump(by_alias=True)
        after_hash = self._hash(data)
        changed = before_hash != after_hash
        story.story_seed = data
        story.story_seed_schema = "story_seed_v1"
        story.story_seed_status = requested_status or story.story_seed_status or "draft"
        story.story_seed_updated_at = datetime.utcnow()
        story.title = seed.title
        story.premise = seed.premise
        story.synopsis = seed.outline
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
