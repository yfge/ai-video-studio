"""Repository queries used by Story CRUD endpoints."""

from app.models.script import Story
from app.models.user import User
from sqlalchemy.orm import Session


class StoryCrudRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_accessible(
        self,
        user: User,
        *,
        genre: str | None,
        status: str | None,
        skip: int,
        limit: int,
    ) -> list[Story]:
        query = self.session.query(Story).filter(Story.is_deleted.is_(False))
        if not user.is_admin and not user.is_superuser:
            query = query.filter(Story.user_id == user.id)
        if genre:
            query = query.filter(Story.genre == genre)
        if status:
            query = query.filter(Story.status == status)
        return query.order_by(Story.id.desc()).offset(skip).limit(limit).all()
