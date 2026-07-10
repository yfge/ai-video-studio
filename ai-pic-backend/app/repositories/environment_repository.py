from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationError
from app.models.story_structure import Environment
from app.models.user import User
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class EnvironmentRepository(BaseRepository[Environment]):
    """Repository for environment asset ownership queries."""

    def __init__(self, session: Session):
        super().__init__(Environment, session)

    def _owned_query(self, user: User):
        query = self.session.query(self.model).filter(self.model.is_deleted.is_(False))
        if not user.is_admin and not user.is_superuser:
            query = query.filter(self.model.user_id == user.id)
        return query

    def get_owned_by_identifier(self, env_id: int | str, user: User) -> Environment:
        if env_id is None or str(env_id).strip() == "":
            raise ValidationError("环境标识缺失", field="environment_id")

        query = self._owned_query(user)
        raw = str(env_id)
        if raw.isdigit():
            query = query.filter(self.model.id == int(raw))
        else:
            query = query.filter(self.model.business_id == raw)

        env = query.first()
        if not env:
            raise NotFoundError("环境", env_id)
        return env

    def find_accessible_by_id(self, env_id: int, user: User) -> Environment | None:
        return self._owned_query(user).filter(self.model.id == env_id).first()

    def list_accessible(
        self,
        *,
        user: User,
        limit: int = 20,
    ) -> list[Environment]:
        """List environment assets visible to a user."""
        return self._owned_query(user).order_by(self.model.id.desc()).limit(limit).all()
