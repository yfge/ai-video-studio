from app.models.llm_invocation import LLMInvocation
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class LLMInvocationRepository(BaseRepository[LLMInvocation]):
    def __init__(self, session: Session):
        super().__init__(LLMInvocation, session)
