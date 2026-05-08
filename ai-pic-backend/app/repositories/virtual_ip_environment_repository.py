from __future__ import annotations

from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session, joinedload


class VirtualIPEnvironmentRepository(BaseRepository[VirtualIPEnvironment]):
    """Repository for IP environment pool links."""

    def __init__(self, session: Session):
        super().__init__(VirtualIPEnvironment, session)

    def list_for_virtual_ip(self, virtual_ip_id: int) -> list[VirtualIPEnvironment]:
        return (
            self.session.query(self.model)
            .options(joinedload(self.model.environment))
            .filter(
                self.model.virtual_ip_id == virtual_ip_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(self.model.sort_order.asc(), self.model.id.asc())
            .all()
        )

    def get_pair(
        self,
        *,
        virtual_ip_id: int,
        environment_id: int,
        include_deleted: bool = False,
    ) -> VirtualIPEnvironment | None:
        query = self.session.query(self.model).filter(
            self.model.virtual_ip_id == virtual_ip_id,
            self.model.environment_id == environment_id,
        )
        if not include_deleted:
            query = query.filter(self.model.is_deleted.is_(False))
        return query.order_by(self.model.is_deleted.asc(), self.model.id.desc()).first()

    def list_for_environment_ids(
        self,
        environment_ids: list[int],
        user: User,
    ) -> list[VirtualIPEnvironment]:
        if not environment_ids:
            return []

        query = (
            self.session.query(self.model)
            .join(VirtualIP, self.model.virtual_ip_id == VirtualIP.id)
            .options(joinedload(self.model.virtual_ip))
            .filter(
                self.model.environment_id.in_(environment_ids),
                self.model.is_deleted.is_(False),
                VirtualIP.is_deleted.is_(False),
            )
        )
        if not user.is_admin and not user.is_superuser:
            query = query.filter(VirtualIP.user_id == user.id)
        return query.order_by(self.model.sort_order.asc(), self.model.id.asc()).all()
