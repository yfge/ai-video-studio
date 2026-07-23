"""Database access for shared character memories and promotion reviews."""

from typing import Optional

from app.models.narrative_memory import CharacterMemory, CharacterMemoryPromotion
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from sqlalchemy import func
from sqlalchemy.orm import Session


class NarrativePromotionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_owned_virtual_ip(self, business_id: str, user: User) -> Optional[VirtualIP]:
        query = self.session.query(VirtualIP).filter(
            VirtualIP.business_id == business_id,
            VirtualIP.is_deleted.is_(False),
        )
        if not user.is_admin and not user.is_superuser:
            query = query.filter(VirtualIP.user_id == user.id)
        return query.first()

    def list_shared_memories(
        self,
        virtual_ip_id: int,
        *,
        canon_branch_id: str = "main",
        include_superseded: bool = False,
    ) -> list[CharacterMemory]:
        query = self.session.query(CharacterMemory).filter(
            CharacterMemory.virtual_ip_id == virtual_ip_id,
            CharacterMemory.canon_branch_id == canon_branch_id,
            CharacterMemory.scope == "character_shared",
            CharacterMemory.is_deleted.is_(False),
        )
        if not include_superseded:
            query = query.filter(CharacterMemory.status == "approved")
        return query.order_by(CharacterMemory.version.desc(), CharacterMemory.id).all()

    def get_shared_memory(
        self, virtual_ip_id: int, business_id: str
    ) -> Optional[CharacterMemory]:
        return (
            self.session.query(CharacterMemory)
            .filter(
                CharacterMemory.virtual_ip_id == virtual_ip_id,
                CharacterMemory.business_id == business_id,
                CharacterMemory.scope == "character_shared",
                CharacterMemory.is_deleted.is_(False),
            )
            .first()
        )

    def next_shared_version(
        self, virtual_ip_id: int, canon_branch_id: str = "main"
    ) -> int:
        value = (
            self.session.query(func.max(CharacterMemory.version))
            .filter(
                CharacterMemory.virtual_ip_id == virtual_ip_id,
                CharacterMemory.canon_branch_id == canon_branch_id,
                CharacterMemory.scope == "character_shared",
            )
            .scalar()
        )
        return int(value or 0) + 1

    def create_shared_memory(self, **data) -> CharacterMemory:
        memory = CharacterMemory(**data)
        self.session.add(memory)
        return memory

    def create_promotion(self, **data) -> CharacterMemoryPromotion:
        promotion = CharacterMemoryPromotion(**data)
        self.session.add(promotion)
        return promotion

    def get_promotion(self, business_id: str) -> Optional[CharacterMemoryPromotion]:
        return (
            self.session.query(CharacterMemoryPromotion)
            .filter(
                CharacterMemoryPromotion.business_id == business_id,
                CharacterMemoryPromotion.is_deleted.is_(False),
            )
            .first()
        )

    def list_promotions(
        self,
        virtual_ip_id: int,
        *,
        canon_branch_id: str = "main",
        status: str | None = None,
    ) -> list[CharacterMemoryPromotion]:
        query = self.session.query(CharacterMemoryPromotion).filter(
            CharacterMemoryPromotion.target_virtual_ip_id == virtual_ip_id,
            CharacterMemoryPromotion.canon_branch_id == canon_branch_id,
            CharacterMemoryPromotion.is_deleted.is_(False),
        )
        if status:
            query = query.filter(CharacterMemoryPromotion.status == status)
        return query.order_by(CharacterMemoryPromotion.id.desc()).all()

    def get_source_memories(
        self, story_id: int, business_ids: list[str]
    ) -> list[CharacterMemory]:
        return (
            self.session.query(CharacterMemory)
            .filter(
                CharacterMemory.story_id == story_id,
                CharacterMemory.business_id.in_(business_ids),
                CharacterMemory.scope == "story_private",
                CharacterMemory.is_deleted.is_(False),
            )
            .all()
        )

    def commit(self) -> None:
        self.session.commit()

    def flush(self) -> None:
        self.session.flush()

    def refresh(self, entity) -> None:
        self.session.refresh(entity)
