"""add_episode_characters_table

Revision ID: 3a9af7b70877
Revises: b4d2c8f1a7e9
Create Date: 2026-02-05 01:58:19.790629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a9af7b70877'
down_revision: Union[str, Sequence[str], None] = 'b4d2c8f1a7e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'episode_characters',
        sa.Column('id', sa.Integer(), nullable=False, comment='Primary key'),
        sa.Column('business_id', sa.String(length=32), nullable=False, comment='Business identifier'),

        # Foreign keys
        sa.Column('episode_id', sa.Integer(), nullable=False, comment='Episode ID'),
        sa.Column('episode_business_id', sa.String(length=32), nullable=True, comment='Business key: episode business_id'),
        sa.Column('virtual_ip_id', sa.Integer(), nullable=False, comment='VirtualIP ID (resource provider)'),
        sa.Column('virtual_ip_business_id', sa.String(length=32), nullable=True, comment='Business key: VirtualIP business_id'),

        # Character metadata
        sa.Column('character_name', sa.String(length=100), nullable=True, comment='Character name (overrides VirtualIP.name)'),
        sa.Column('role_type', sa.String(length=50), nullable=True, server_default='temporary', comment='Role type: temporary/guest/extra'),
        sa.Column('importance', sa.Integer(), nullable=True, server_default='1', comment='Importance level 1-5, default 1'),

        # Override fields
        sa.Column('personality', sa.Text(), nullable=True, comment='Personality (overrides VirtualIP)'),
        sa.Column('background', sa.Text(), nullable=True, comment='Background (overrides VirtualIP)'),
        sa.Column('appearance_override', sa.Text(), nullable=True, comment='Appearance supplement to VirtualIP.style_prompt'),
        sa.Column('voice_config_override', sa.JSON(), nullable=True, comment='Voice config override (replaces VirtualIP.voice_config)'),

        # Scene tracking
        sa.Column('scene_appearances', sa.JSON(), nullable=True, comment='List of scene appearances: [{scene_number, role_in_scene}]'),
        sa.Column('first_appearance_scene', sa.Integer(), nullable=True, comment='First appearance scene number'),
        sa.Column('last_appearance_scene', sa.Integer(), nullable=True, comment='Last appearance scene number'),

        sa.Column('extra_metadata', sa.JSON(), nullable=True, comment='Additional metadata'),

        # Soft delete fields
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0', comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Deletion timestamp'),
        sa.Column('deleted_by', sa.Integer(), nullable=True, comment='User who deleted'),
        sa.Column('deleted_reason', sa.Text(), nullable=True, comment='Deletion reason'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Creation time'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Update time'),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['virtual_ip_id'], ['virtual_ips.id'], ondelete='RESTRICT'),
    )

    # Create indexes
    op.create_index('idx_episode_id', 'episode_characters', ['episode_id'])
    op.create_index('idx_virtual_ip_id', 'episode_characters', ['virtual_ip_id'])
    op.create_index('idx_is_deleted', 'episode_characters', ['is_deleted'])
    op.create_index(op.f('ix_episode_characters_business_id'), 'episode_characters', ['business_id'], unique=True)
    op.create_index(op.f('ix_episode_characters_episode_business_id'), 'episode_characters', ['episode_business_id'])
    op.create_index(op.f('ix_episode_characters_virtual_ip_business_id'), 'episode_characters', ['virtual_ip_business_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_episode_characters_virtual_ip_business_id'), table_name='episode_characters')
    op.drop_index(op.f('ix_episode_characters_episode_business_id'), table_name='episode_characters')
    op.drop_index(op.f('ix_episode_characters_business_id'), table_name='episode_characters')
    op.drop_index('idx_is_deleted', table_name='episode_characters')
    op.drop_index('idx_virtual_ip_id', table_name='episode_characters')
    op.drop_index('idx_episode_id', table_name='episode_characters')
    op.drop_table('episode_characters')
