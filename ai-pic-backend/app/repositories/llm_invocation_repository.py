from app.models.llm_invocation import LLMInvocation
from app.repositories.base import BaseRepository
from sqlalchemy import or_
from sqlalchemy.orm import Session


class LLMInvocationRepository(BaseRepository[LLMInvocation]):
    def __init__(self, session: Session):
        super().__init__(LLMInvocation, session)

    def list_by_call_scene_prefix(self, prefix: str) -> list[LLMInvocation]:
        return (
            self.session.query(LLMInvocation)
            .filter(
                or_(
                    LLMInvocation.call_scene == prefix,
                    LLMInvocation.call_scene.startswith(f"{prefix}."),
                )
            )
            .order_by(LLMInvocation.id)
            .all()
        )
