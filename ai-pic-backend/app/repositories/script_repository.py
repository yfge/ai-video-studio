"""
Script repository for data access layer.

Encapsulates all database operations for Script, Episode, and Story models,
providing clean separation between business logic and data access.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models.script import Script, Episode, Story
from app.repositories.base import BaseRepository


class ScriptRepository(BaseRepository[Script]):
    """
    Repository for Script model operations.

    Provides methods for querying scripts with their related
    episodes and stories, supporting user-based filtering.
    """

    def __init__(self, session: Session):
        super().__init__(Script, session)

    def get_with_relations(
        self,
        script_id: Optional[int] = None,
        business_id: Optional[str] = None,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Script]:
        """
        Get script with episode and story relations loaded.

        Args:
            script_id: Script primary key
            business_id: Script business ID
            user_id: Filter by story owner (optional)
            include_deleted: Include soft-deleted records

        Returns:
            Script with relations or None
        """
        query = (
            self.session.query(Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .options(joinedload(Script.episode).joinedload(Episode.story))
        )

        if not include_deleted:
            query = query.filter(Script.is_deleted.is_(False))
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if script_id is not None:
            query = query.filter(Script.id == script_id)
        elif business_id is not None:
            query = query.filter(Script.business_id == business_id)
        else:
            return None

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return query.first()

    def list_by_episode(
        self,
        episode_id: Optional[int] = None,
        episode_business_id: Optional[str] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        format_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Script]:
        """
        List scripts by episode with optional filters.

        Args:
            episode_id: Filter by episode ID
            episode_business_id: Filter by episode business ID
            user_id: Filter by story owner
            status: Filter by script status
            format_type: Filter by format type
            skip: Pagination offset
            limit: Max results
            include_deleted: Include soft-deleted records

        Returns:
            List of Script instances
        """
        query = (
            self.session.query(Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
        )

        if not include_deleted:
            query = query.filter(Script.is_deleted.is_(False))
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if episode_id is not None:
            query = query.filter(Script.episode_id == episode_id)
        if episode_business_id is not None:
            query = query.filter(Episode.business_id == episode_business_id)
        if status is not None:
            query = query.filter(Script.status == status)
        if format_type is not None:
            query = query.filter(Script.format_type == format_type)
        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return (
            query.order_by(Script.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_storyboard(
        self,
        script_id: int,
        storyboard_data: Dict[str, Any],
        increment_version: bool = True
    ) -> Optional[Script]:
        """
        Update script storyboard data.

        Args:
            script_id: Script primary key
            storyboard_data: New storyboard data to merge into extra_metadata
            increment_version: Whether to increment storyboard version

        Returns:
            Updated Script or None if not found
        """
        script = self.get_by_id(script_id)
        if script is None:
            return None

        extra = script.extra_metadata or {}
        extra["storyboard"] = storyboard_data
        script.extra_metadata = extra
        script.storyboard_updated_at = datetime.utcnow()

        if increment_version:
            script.storyboard_version = (script.storyboard_version or 0) + 1

        return script

    def update_storyboard_plan(
        self,
        script_id: int,
        plan_data: Dict[str, Any]
    ) -> Optional[Script]:
        """
        Update script storyboard plan.

        Args:
            script_id: Script primary key
            plan_data: New storyboard plan data

        Returns:
            Updated Script or None if not found
        """
        script = self.get_by_id(script_id)
        if script is None:
            return None

        script.storyboard_plan = plan_data
        script.storyboard_updated_at = datetime.utcnow()
        return script


class EpisodeRepository(BaseRepository[Episode]):
    """
    Repository for Episode model operations.

    Provides methods for querying episodes with their related stories.
    """

    def __init__(self, session: Session):
        super().__init__(Episode, session)

    def get_with_story(
        self,
        episode_id: Optional[int] = None,
        business_id: Optional[str] = None,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Episode]:
        """
        Get episode with story relation loaded.

        Args:
            episode_id: Episode primary key
            business_id: Episode business ID
            user_id: Filter by story owner
            include_deleted: Include soft-deleted records

        Returns:
            Episode with story or None
        """
        query = (
            self.session.query(Episode)
            .join(Story, Episode.story_id == Story.id)
            .options(joinedload(Episode.story))
        )

        if not include_deleted:
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if episode_id is not None:
            query = query.filter(Episode.id == episode_id)
        elif business_id is not None:
            query = query.filter(Episode.business_id == business_id)
        else:
            return None

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return query.first()

    def list_by_story(
        self,
        story_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> List[Episode]:
        """
        List episodes by story.

        Args:
            story_id: Story ID
            user_id: Filter by story owner
            include_deleted: Include soft-deleted records

        Returns:
            List of Episode instances ordered by episode number
        """
        query = (
            self.session.query(Episode)
            .join(Story, Episode.story_id == Story.id)
            .filter(Episode.story_id == story_id)
        )

        if not include_deleted:
            query = query.filter(Episode.is_deleted.is_(False))
            query = query.filter(Story.is_deleted.is_(False))

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return query.order_by(Episode.episode_number).all()


class StoryRepository(BaseRepository[Story]):
    """
    Repository for Story model operations.

    Provides methods for querying stories with user-based filtering.
    """

    def __init__(self, session: Session):
        super().__init__(Story, session)

    def list_by_user(
        self,
        user_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Story]:
        """
        List stories by user.

        Args:
            user_id: User ID
            status: Filter by status
            skip: Pagination offset
            limit: Max results
            include_deleted: Include soft-deleted records

        Returns:
            List of Story instances
        """
        query = self.session.query(Story).filter(Story.user_id == user_id)

        if not include_deleted:
            query = query.filter(Story.is_deleted.is_(False))

        if status is not None:
            query = query.filter(Story.status == status)

        return (
            query.order_by(Story.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self,
        story_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False
    ) -> Optional[Story]:
        """
        Get story with optional user filter.

        Args:
            story_id: Story ID
            user_id: Filter by owner (optional)
            include_deleted: Include soft-deleted records

        Returns:
            Story or None
        """
        query = self.session.query(Story).filter(Story.id == story_id)

        if not include_deleted:
            query = query.filter(Story.is_deleted.is_(False))

        if user_id is not None:
            query = query.filter(Story.user_id == user_id)

        return query.first()
