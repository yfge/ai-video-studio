"""Repository queries for story environment readiness checks."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.script import Episode, Script, StoryCharacter
from app.models.story_structure import Scene
from app.models.virtual_ip import VirtualIPEnvironment
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SceneEnvironmentCoverage:
    total: int
    bound: int


class StoryEnvironmentReadinessRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_story_virtual_ip_ids(self, story_id: int) -> list[int]:
        rows = (
            self.session.query(StoryCharacter.virtual_ip_id)
            .filter(
                StoryCharacter.story_id == story_id,
                StoryCharacter.is_deleted.is_(False),
            )
            .all()
        )
        return sorted({row.virtual_ip_id for row in rows if row.virtual_ip_id})

    def count_linked_environments(self, virtual_ip_ids: list[int]) -> int:
        if not virtual_ip_ids:
            return 0
        return (
            self.session.query(VirtualIPEnvironment.id)
            .filter(
                VirtualIPEnvironment.virtual_ip_id.in_(virtual_ip_ids),
                VirtualIPEnvironment.is_deleted.is_(False),
            )
            .count()
        )

    def list_story_script_ids(self, story_id: int) -> list[int]:
        rows = (
            self.session.query(Script.id)
            .join(Episode, Script.episode_id == Episode.id)
            .filter(
                Episode.story_id == story_id,
                Episode.is_deleted.is_(False),
                Script.is_deleted.is_(False),
            )
            .all()
        )
        return [row.id for row in rows]

    def get_scene_environment_coverage(
        self, script_ids: list[int]
    ) -> SceneEnvironmentCoverage | None:
        if not script_ids:
            return None
        rows = (
            self.session.query(Scene.id, Scene.environment_id)
            .filter(
                Scene.script_id.in_(script_ids),
                Scene.is_deleted.is_(False),
            )
            .all()
        )
        if not rows:
            return None
        return SceneEnvironmentCoverage(
            total=len(rows),
            bound=sum(1 for row in rows if row.environment_id),
        )
