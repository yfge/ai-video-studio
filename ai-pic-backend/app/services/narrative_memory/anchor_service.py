"""Narrative anchor creation and validation."""

from app.core.exceptions import ValidationError
from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_memory import NarrativeAnchorCreate


class AnchorService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def create(
        self,
        story: Story,
        payload: NarrativeAnchorCreate,
        user_id: int,
        *,
        commit: bool = True,
    ):
        data = payload.model_dump()
        self._validate_between(story, data)
        anchor = self.repo.create_anchor(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            **data,
        )
        if commit:
            self.repo.commit()
            self.repo.refresh(anchor)
        return anchor

    def _validate_between(self, story: Story, data: dict) -> None:
        if data["anchor_type"] != "between":
            return
        after = self.repo.get_anchor(story.id, data["after_anchor_business_id"])
        before = self.repo.get_anchor(story.id, data["before_anchor_business_id"])
        if not after or not before:
            raise ValidationError("离场事件的前后锚点必须属于当前 Story")
        if after.narrative_sequence >= before.narrative_sequence:
            raise ValidationError("离场事件的前锚点必须早于后锚点")
