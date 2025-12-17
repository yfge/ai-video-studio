import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text


def generate_business_id() -> str:
    """Generate a 32-char business identifier (replace(uuid(), '-', '') semantics)."""
    return uuid.uuid4().hex


class SoftDeleteBusinessMixin:
    """Shared mixin providing business_id and soft delete fields."""

    __abstract__ = True

    business_id = Column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        default=generate_business_id,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    deleted_reason = Column(Text, nullable=True)

    def soft_delete(self, *, user_id: int | None = None, reason: str | None = None):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if user_id is not None:
            self.deleted_by = user_id
        if reason:
            self.deleted_reason = reason
