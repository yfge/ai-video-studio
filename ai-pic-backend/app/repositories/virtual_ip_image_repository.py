from __future__ import annotations

from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class VirtualIPImageRepository(BaseRepository[VirtualIPImage]):
    def __init__(self, session: Session):
        super().__init__(VirtualIPImage, session)

    def find_accessible_by_result_ref(
        self,
        *,
        image_id: int,
        virtual_ip_id: int,
        user: User,
    ) -> VirtualIPImage | None:
        query = (
            self.session.query(self.model)
            .join(VirtualIP, VirtualIP.id == self.model.virtual_ip_id)
            .filter(
                self.model.id == image_id,
                self.model.virtual_ip_id == virtual_ip_id,
                self.model.is_deleted.is_(False),
                VirtualIP.is_deleted.is_(False),
            )
        )
        if not user.is_admin and not user.is_superuser:
            query = query.filter(VirtualIP.user_id == user.id)
        return query.first()
