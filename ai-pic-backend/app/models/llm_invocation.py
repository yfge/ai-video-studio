from app.core.database import Base
from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import func

LONG_TEXT = Text().with_variant(mysql.LONGTEXT(), "mysql")


class LLMInvocation(Base):
    """One application-level attempt to invoke an AI generation provider."""

    __tablename__ = "llm_invocations"

    id = Column(Integer, primary_key=True, index=True)
    invocation_type = Column(String(32), nullable=False, default="text", index=True)
    call_scene = Column(String(512), nullable=False, index=True)
    provider = Column(String(64), nullable=False, index=True)
    model = Column(String(255), nullable=True, index=True)
    attempt_index = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="processing", index=True)

    original_prompt = Column(LONG_TEXT, nullable=False)
    prompt = Column(LONG_TEXT, nullable=False)
    system_prompt = Column(LONG_TEXT, nullable=True)
    response = Column(LONG_TEXT, nullable=True)
    error = Column(LONG_TEXT, nullable=True)

    request_parameters = Column(JSON, nullable=True)
    input_references = Column(JSON, nullable=True)
    output_assets = Column(JSON, nullable=True)
    usage = Column(JSON, nullable=True)
    response_metadata = Column(JSON, nullable=True)
    provider_task_id = Column(String(512), nullable=True, index=True)
    input_tokens = Column(BigInteger, nullable=True)
    cache_tokens = Column(BigInteger, nullable=True)
    output_tokens = Column(BigInteger, nullable=True)

    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Integer, nullable=True)
