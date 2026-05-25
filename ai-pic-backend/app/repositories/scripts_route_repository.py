"""Repository helpers for script endpoint routes."""

from __future__ import annotations

from typing import Optional

from app.models.script import Episode, Script, Story
from app.models.user import User
from sqlalchemy.orm import Session, load_only

SCRIPT_LIST_COLUMNS = (
    Script.id,
    Script.business_id,
    Script.episode_id,
    Script.episode_business_id,
    Script.title,
    Script.format_type,
    Script.language,
    Script.status,
    Script.version,
    Script.tags,
    Script.page_count,
    Script.word_count,
    Script.character_count,
    Script.ai_model,
    Script.created_at,
    Script.updated_at,
)


class ScriptsRouteRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def not_deleted(query, model):
        return query.filter(model.is_deleted.is_(False))

    def get_script_by_identifier(
        self,
        *,
        script_id: Optional[int],
        script_business_id: Optional[str],
        current_user: User,
    ) -> Script | None:
        query = (
            self.not_deleted(self.db.query(Script), Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .filter(Episode.is_deleted.is_(False))
            .filter(Story.is_deleted.is_(False))
        )
        if script_business_id:
            query = query.filter(Script.business_id == script_business_id)
        elif script_id:
            query = query.filter(Script.id == script_id)
        else:
            return None

        if not current_user.is_admin and not current_user.is_superuser:
            query = query.filter(Story.user_id == current_user.id)
        return query.first()

    def list_scripts(
        self,
        *,
        episode_id: Optional[int],
        episode_business_id: Optional[str],
        skip: int,
        limit: int,
        status: Optional[str],
        format_type: Optional[str],
        current_user: User,
    ) -> list[Script]:
        base_query = (
            self.not_deleted(self.db.query(Script), Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .filter(Episode.is_deleted.is_(False))
            .filter(Story.is_deleted.is_(False))
        )
        if episode_id:
            base_query = base_query.filter(Script.episode_id == episode_id)
        if episode_business_id:
            base_query = base_query.filter(Episode.business_id == episode_business_id)
        if status:
            base_query = base_query.filter(Script.status == status)
        if format_type:
            base_query = base_query.filter(Script.format_type == format_type)
        if not current_user.is_admin and not current_user.is_superuser:
            base_query = base_query.filter(Story.user_id == current_user.id)

        id_subquery = (
            base_query.with_entities(Script.id)
            .order_by(Script.id.desc())
            .offset(skip)
            .limit(limit)
            .subquery()
        )
        return (
            self.not_deleted(self.db.query(Script), Script)
            .options(load_only(*SCRIPT_LIST_COLUMNS))
            .join(id_subquery, Script.id == id_subquery.c.id)
            .order_by(Script.id.desc())
            .all()
        )

    def get_episode_for_user(
        self,
        *,
        episode_id: int | None = None,
        episode_business_id: str | None = None,
        current_user: User,
    ) -> Episode | None:
        query = self.not_deleted(self.db.query(Episode), Episode).join(
            Story, Episode.story_id == Story.id
        )
        if not current_user.is_admin and not current_user.is_superuser:
            query = query.filter(Story.user_id == current_user.id)
        if episode_business_id:
            query = query.filter(Episode.business_id == episode_business_id)
        if episode_id is not None:
            query = query.filter(Episode.id == episode_id)
        if episode_business_id or episode_id is not None:
            return query.first()
        return None

    def get_prompt_preview_episode(
        self,
        *,
        episode_id: int,
        current_user: User,
    ) -> Episode | None:
        query = self.db.query(Episode).join(Story, Episode.story_id == Story.id)
        if not current_user.is_admin and not current_user.is_superuser:
            query = query.filter(Story.user_id == current_user.id)
        return query.filter(Episode.id == episode_id).first()

    def get_create_episode(
        self,
        *,
        episode_id: int,
        current_user: User,
    ) -> Episode | None:
        query = self.not_deleted(self.db.query(Episode), Episode).join(
            Story, Episode.story_id == Story.id
        )
        if not current_user.is_admin and not current_user.is_superuser:
            query = query.filter(Story.user_id == current_user.id)
        return query.filter(Episode.id == episode_id).first()

    def list_scripts_for_episode(self, episode_id: int) -> list[Script]:
        return (
            self.not_deleted(self.db.query(Script), Script)
            .options(load_only(*SCRIPT_LIST_COLUMNS))
            .filter(Script.episode_id == episode_id)
            .limit(50)
            .all()
        )

    def get_export_script(self, *, script_id: int, current_user: User) -> Script | None:
        return (
            self.db.query(Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .filter(Script.id == script_id)
            .filter(
                True
                if current_user.is_admin or current_user.is_superuser
                else Story.user_id == current_user.id
            )
            .first()
        )
