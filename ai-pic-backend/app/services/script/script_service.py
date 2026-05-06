"""Script CRUD service."""

from typing import List, Optional

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.user import User
from app.repositories.script_repository import (
    EpisodeRepository,
    ScriptRepository,
    StoryRepository,
)
from app.schemas.script import ScriptCreate, ScriptUpdate
from sqlalchemy.orm import Session

logger = get_logger()


class ScriptService:
    """Script business operations backed by repositories."""

    def __init__(self, session: Session):
        self.session = session
        self.script_repo = ScriptRepository(session)
        self.episode_repo = EpisodeRepository(session)
        self.story_repo = StoryRepository(session)

    def _get_user_id_filter(self, user: User) -> Optional[int]:
        """Get user ID for filtering, None for admins."""
        if user.is_admin or user.is_superuser:
            return None
        return user.id

    def _check_user_access(
        self,
        user: User,
        story: Optional[Story] = None,
        episode: Optional[Episode] = None,
    ) -> bool:
        if user.is_admin or user.is_superuser:
            return True
        if story and story.user_id == user.id:
            return True
        if episode and episode.story and episode.story.user_id == user.id:
            return True
        return False

    def get_script(
        self,
        script_id: Optional[int] = None,
        business_id: Optional[str] = None,
        user: Optional[User] = None,
    ) -> Script:
        """Get script by ID or business_id."""
        user_id = self._get_user_id_filter(user) if user else None
        script = self.script_repo.get_with_relations(
            script_id=script_id, business_id=business_id, user_id=user_id
        )
        if not script:
            raise NotFoundError("剧本", script_id or business_id)
        return script

    def list_scripts(
        self,
        user: User,
        episode_id: Optional[int] = None,
        episode_business_id: Optional[str] = None,
        status: Optional[str] = None,
        format_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Script]:
        """List scripts with filters."""
        user_id = self._get_user_id_filter(user)
        return self.script_repo.list_by_episode(
            episode_id=episode_id,
            episode_business_id=episode_business_id,
            user_id=user_id,
            status=status,
            format_type=format_type,
            skip=skip,
            limit=limit,
        )

    def get_episode_scripts(
        self, episode_id: int, user: User, limit: int = 50
    ) -> List[Script]:
        """Get scripts for an episode."""
        user_id = self._get_user_id_filter(user)
        episode = self.episode_repo.get_with_story(
            episode_id=episode_id, user_id=user_id
        )
        if not episode:
            raise NotFoundError("剧集", episode_id)

        return self.script_repo.list_by_episode(
            episode_id=episode_id, user_id=user_id, limit=limit
        )

    def create_script(self, script_data: ScriptCreate, user: User) -> Script:
        """Create a new script."""
        user_id = self._get_user_id_filter(user)
        episode = self.episode_repo.get_with_story(
            episode_id=script_data.episode_id, user_id=user_id
        )
        if not episode:
            raise NotFoundError("剧集", script_data.episode_id)

        word_count = len(script_data.content.split()) if script_data.content else 0
        character_count = len(script_data.content) if script_data.content else 0

        script = self.script_repo.create(
            **script_data.dict(), word_count=word_count, character_count=character_count
        )
        self.session.commit()
        self.session.refresh(script)

        self._sync_scenes_safe(script)
        return script

    def update_script(
        self,
        script_id: Optional[int] = None,
        business_id: Optional[str] = None,
        update_data: ScriptUpdate = None,
        user: Optional[User] = None,
    ) -> Script:
        """Update an existing script."""
        script = self.get_script(
            script_id=script_id, business_id=business_id, user=user
        )

        update_dict = update_data.dict(exclude_unset=True) if update_data else {}
        for field, value in update_dict.items():
            setattr(script, field, value)

        if update_data and update_data.content:
            script.word_count = len(update_data.content.split())
            script.character_count = len(update_data.content)
            script.page_count = max(1, script.character_count // 2000)

        self.session.commit()
        self.session.refresh(script)

        self._sync_scenes_safe(script)
        return script

    def delete_script(
        self,
        script_id: Optional[int] = None,
        business_id: Optional[str] = None,
        user: Optional[User] = None,
        reason: str = "user delete",
    ) -> None:
        """Soft delete a script."""
        script = self.get_script(
            script_id=script_id, business_id=business_id, user=user
        )

        user_id = user.id if user else None
        script.soft_delete(user_id=user_id, reason=reason)
        self.session.commit()

    def _sync_scenes_safe(self, script: Script) -> None:
        """Best-effort normalized scene sync."""
        try:
            from app.services.script.story_structure_sync import (
                sync_script_scenes_to_story_structure,
            )

            sync_script_scenes_to_story_structure(self.session, script)
        except Exception:
            logger.warning("同步规范化场景失败", exc_info=True)


def get_script_service(session: Session) -> ScriptService:
    return ScriptService(session)
