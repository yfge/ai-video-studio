"""
Virtual IP repository for data access layer.

Encapsulates VirtualIP queries with ownership and soft-delete filters.
"""

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class VirtualIPRepository(BaseRepository[VirtualIP]):
    """Repository for VirtualIP model operations."""

    def __init__(self, session: Session):
        super().__init__(VirtualIP, session)

    def _owned_query(self, user: User):
        query = self.session.query(self.model).filter(self.model.is_deleted.is_(False))
        if not user.is_admin and not user.is_superuser:
            query = query.filter(self.model.user_id == user.id)
        return query

    def get_owned_by_id(self, ip_id: int, user: User) -> VirtualIP:
        if ip_id is None:
            raise ValidationError("虚拟IP标识缺失", field="virtual_ip_id")
        ip = self._owned_query(user).filter(self.model.id == ip_id).first()
        if not ip:
            raise NotFoundError.virtual_ip(ip_id)
        return ip

    def get_owned_by_business_id(self, business_id: str, user: User) -> VirtualIP:
        if not business_id:
            raise ValidationError("虚拟IP标识缺失", field="virtual_ip_business_id")
        ip = (
            self._owned_query(user)
            .filter(self.model.business_id == business_id)
            .first()
        )
        if not ip:
            raise NotFoundError.virtual_ip(business_id)
        return ip

    def find_accessible_by_id(
        self,
        ip_id: int,
        *,
        user: User | None = None,
        user_id: int | None = None,
    ) -> VirtualIP | None:
        query = self.session.query(self.model).filter(
            self.model.id == ip_id,
            self.model.is_deleted.is_(False),
        )
        if user is not None and not user.is_admin and not user.is_superuser:
            query = query.filter(self.model.user_id == user.id)
        elif user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        return query.first()

    def list_accessible(
        self,
        *,
        user: User,
        limit: int = 20,
    ) -> list[VirtualIP]:
        """List active Virtual IP assets visible to a user."""
        query = self._owned_query(user).filter(self.model.is_active.is_(True))
        return query.order_by(self.model.id.desc()).limit(limit).all()
