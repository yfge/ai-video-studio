"""Add user management fields

Revision ID: 0002_add_user_management_fields
Revises: 919189f166fc
Create Date: 2025-01-25 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_user_management_fields"
down_revision: Union[str, Sequence[str], None] = "919189f166fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user management fields to users table and create user_audit_logs table."""

    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if is_sqlite:
        # SQLite doesn't support ALTER TABLE ADD CONSTRAINT; use batch mode.
        with op.batch_alter_table("users") as batch_op:
            batch_op.add_column(
                sa.Column("is_admin", sa.Boolean(), default=False, comment="是否为管理员")
            )
            batch_op.add_column(
                sa.Column(
                    "is_approved", sa.Boolean(), default=False, comment="是否已审批通过"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "approved_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="审批时间",
                )
            )
            batch_op.add_column(
                sa.Column(
                    "approved_by_user_id", sa.Integer(), nullable=True, comment="审批人ID"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "email_verified", sa.Boolean(), default=False, comment="邮箱是否已验证"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "activation_token", sa.String(255), nullable=True, comment="激活令牌"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "activation_token_expires",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="激活令牌过期时间",
                )
            )
            batch_op.add_column(
                sa.Column(
                    "last_login_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="最后登录时间",
                )
            )
            batch_op.add_column(
                sa.Column(
                    "failed_login_attempts", sa.Integer(), default=0, comment="失败登录次数"
                )
            )
            batch_op.add_column(
                sa.Column(
                    "account_locked_until",
                    sa.DateTime(timezone=True),
                    nullable=True,
                    comment="账户锁定到期时间",
                )
            )
            batch_op.add_column(
                sa.Column("language", sa.String(10), default="zh-CN", comment="用户语言偏好")
            )
            batch_op.add_column(
                sa.Column(
                    "timezone", sa.String(50), default="Asia/Shanghai", comment="用户时区"
                )
            )

            batch_op.create_foreign_key(
                "fk_users_approved_by_user_id",
                "users",
                ["approved_by_user_id"],
                ["id"],
            )

            # Change is_active default to FALSE for new registrations.
            batch_op.alter_column(
                "is_active",
                existing_type=sa.Boolean(),
                server_default=sa.text("FALSE"),
            )
    else:
        # Add new fields to users table
        op.add_column(
            "users",
            sa.Column("is_admin", sa.Boolean(), default=False, comment="是否为管理员"),
        )
        op.add_column(
            "users",
            sa.Column(
                "is_approved", sa.Boolean(), default=False, comment="是否已审批通过"
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "approved_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="审批时间",
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "approved_by_user_id", sa.Integer(), nullable=True, comment="审批人ID"
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "email_verified", sa.Boolean(), default=False, comment="邮箱是否已验证"
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "activation_token", sa.String(255), nullable=True, comment="激活令牌"
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "activation_token_expires",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="激活令牌过期时间",
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "last_login_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="最后登录时间",
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "failed_login_attempts", sa.Integer(), default=0, comment="失败登录次数"
            ),
        )
        op.add_column(
            "users",
            sa.Column(
                "account_locked_until",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="账户锁定到期时间",
            ),
        )
        op.add_column(
            "users",
            sa.Column("language", sa.String(10), default="zh-CN", comment="用户语言偏好"),
        )
        op.add_column(
            "users",
            sa.Column(
                "timezone", sa.String(50), default="Asia/Shanghai", comment="用户时区"
            ),
        )

        # Add foreign key constraint
        op.create_foreign_key(
            "fk_users_approved_by_user_id",
            "users",
            "users",
            ["approved_by_user_id"],
            ["id"],
        )

    # Update existing users to have default values
    op.execute(
        """
        UPDATE users SET
            is_admin = FALSE,
            is_approved = TRUE,  -- Existing users are approved by default
            email_verified = TRUE,  -- Existing users have verified emails by default
            failed_login_attempts = 0,
            language = 'zh-CN',
            timezone = 'Asia/Shanghai'
        WHERE TRUE
    """
    )

    # Change is_active default to FALSE for new registrations
    if not is_sqlite:
        op.alter_column("users", "is_active", server_default=sa.text("FALSE"))

    # Create user_audit_logs table
    op.create_table(
        "user_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="被操作用户ID"),
        sa.Column("admin_user_id", sa.Integer(), nullable=True, comment="操作管理员ID"),
        sa.Column("action", sa.String(50), nullable=False, comment="操作类型"),
        sa.Column("old_values", sa.Text(), nullable=True, comment="操作前的值(JSON)"),
        sa.Column("new_values", sa.Text(), nullable=True, comment="操作后的值(JSON)"),
        sa.Column("ip_address", sa.String(45), nullable=True, comment="IP地址"),
        sa.Column("user_agent", sa.String(500), nullable=True, comment="用户代理"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            comment="操作时间",
        ),
        sa.ForeignKeyConstraint(
            ["admin_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_audit_logs_id"), "user_audit_logs", ["id"], unique=False
    )


def downgrade() -> None:
    """Remove user management fields and user_audit_logs table."""

    # Drop user_audit_logs table
    op.drop_index(op.f("ix_user_audit_logs_id"), table_name="user_audit_logs")
    op.drop_table("user_audit_logs")

    # Drop foreign key constraint
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    if is_sqlite:
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_constraint(
                "fk_users_approved_by_user_id", type_="foreignkey"
            )
            batch_op.drop_column("timezone")
            batch_op.drop_column("language")
            batch_op.drop_column("account_locked_until")
            batch_op.drop_column("failed_login_attempts")
            batch_op.drop_column("last_login_at")
            batch_op.drop_column("activation_token_expires")
            batch_op.drop_column("activation_token")
            batch_op.drop_column("email_verified")
            batch_op.drop_column("approved_by_user_id")
            batch_op.drop_column("approved_at")
            batch_op.drop_column("is_approved")
            batch_op.drop_column("is_admin")
            batch_op.alter_column(
                "is_active",
                existing_type=sa.Boolean(),
                server_default=sa.text("TRUE"),
            )
    else:
        op.drop_constraint("fk_users_approved_by_user_id", "users", type_="foreignkey")

        # Remove columns from users table
        op.drop_column("users", "timezone")
        op.drop_column("users", "language")
        op.drop_column("users", "account_locked_until")
        op.drop_column("users", "failed_login_attempts")
        op.drop_column("users", "last_login_at")
        op.drop_column("users", "activation_token_expires")
        op.drop_column("users", "activation_token")
        op.drop_column("users", "email_verified")
        op.drop_column("users", "approved_by_user_id")
        op.drop_column("users", "approved_at")
        op.drop_column("users", "is_approved")
        op.drop_column("users", "is_admin")

        # Restore is_active default
        op.alter_column("users", "is_active", server_default=sa.text("TRUE"))
