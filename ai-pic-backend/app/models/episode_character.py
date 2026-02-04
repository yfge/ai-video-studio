from datetime import datetime

from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class EpisodeCharacter(SoftDeleteBusinessMixin, Base):
    """Episode temporary character model - binds VirtualIPs to Episodes for temporary roles."""

    __tablename__ = "episode_characters"
    __table_args__ = (
        Index("idx_episode_id", "episode_id"),
        Index("idx_virtual_ip_id", "virtual_ip_id"),
        Index("idx_is_deleted", "is_deleted"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    episode_id = Column(
        Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, comment="Episode ID"
    )
    episode_business_id = Column(
        String(32), index=True, nullable=True, comment="Business key: episode business_id"
    )
    virtual_ip_id = Column(
        Integer,
        ForeignKey("virtual_ips.id", ondelete="RESTRICT"),
        nullable=False,
        comment="VirtualIP ID (resource provider)",
    )
    virtual_ip_business_id = Column(
        String(32), index=True, nullable=True, comment="Business key: VirtualIP business_id"
    )

    # Character metadata
    character_name = Column(
        String(100), nullable=True, comment="Character name (overrides VirtualIP.name)"
    )
    role_type = Column(
        String(50), default="temporary", comment="Role type: temporary/guest/extra"
    )
    importance = Column(Integer, default=1, comment="Importance level 1-5, default 1")

    # Override fields (optional)
    personality = Column(Text, nullable=True, comment="Personality (overrides VirtualIP)")
    background = Column(Text, nullable=True, comment="Background (overrides VirtualIP)")
    appearance_override = Column(
        Text, nullable=True, comment="Appearance supplement to VirtualIP.style_prompt"
    )
    voice_config_override = Column(
        JSON, nullable=True, comment="Voice config override (replaces VirtualIP.voice_config)"
    )

    # Scene tracking
    scene_appearances = Column(
        JSON,
        nullable=True,
        comment="List of scene appearances: [{scene_number, role_in_scene}]",
    )
    first_appearance_scene = Column(Integer, nullable=True, comment="First appearance scene number")
    last_appearance_scene = Column(Integer, nullable=True, comment="Last appearance scene number")

    extra_metadata = Column(JSON, nullable=True, comment="Additional metadata")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment="Creation time")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Update time"
    )

    # Relationships
    episode = relationship("Episode", back_populates="episode_characters")
    virtual_ip = relationship("VirtualIP")
