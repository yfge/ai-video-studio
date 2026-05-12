from __future__ import annotations

from app.models.user import User
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class UserRepository(BaseRepository[User]):
    """Repository for user lookup operations."""

    def __init__(self, session: Session):
        super().__init__(User, session)
