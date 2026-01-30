from app.core.database import Base
from app.models.base import SoftDeleteBusinessMixin
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime


class User(SoftDeleteBusinessMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ux_users_email_is_deleted", "email", "is_deleted", unique=True),
        Index("ux_users_username_is_deleted", "username", "is_deleted", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)

    # 基础状态字段
    is_active = Column(Boolean, default=False, comment="账户是否激活（默认未激活）")
    is_superuser = Column(Boolean, default=False, comment="是否为超级用户")
    is_admin = Column(Boolean, default=False, comment="是否为管理员")

    # 用户审批相关
    is_approved = Column(Boolean, default=False, comment="是否已审批通过")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审批时间")
    approved_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审批人ID"
    )

    # 邮箱验证相关
    email_verified = Column(Boolean, default=False, comment="邮箱是否已验证")
    activation_token = Column(String(255), nullable=True, comment="激活令牌")
    activation_token_expires = Column(
        DateTime(timezone=True), nullable=True, comment="激活令牌过期时间"
    )

    # 登录相关
    last_login_at = Column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    account_locked_until = Column(
        DateTime(timezone=True), nullable=True, comment="账户锁定到期时间"
    )

    # 用户偏好
    language = Column(String(10), default="zh-CN", comment="用户语言偏好")
    timezone = Column(String(50), default="Asia/Shanghai", comment="用户时区")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 关系
    images = relationship("Image", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    approved_by = relationship("User", remote_side=[id], backref="approved_users")
    virtual_ips = relationship("VirtualIP", backref="owner")
    stories = relationship("Story", backref="owner")
    environments = relationship("Environment", backref="owner")

    @property
    def can_login(self):
        """检查用户是否可以登录"""
        return (
            self.is_active
            and self.is_approved
            and self.email_verified
            and (
                self.account_locked_until is None
                or self.account_locked_until < datetime.utcnow()
            )
        )

    @property
    def is_account_locked(self):
        """检查账户是否被锁定"""
        return (
            self.account_locked_until is not None
            and self.account_locked_until > datetime.utcnow()
        )

    def __str__(self) -> str:
        return self.username


class UserAuditLog(SoftDeleteBusinessMixin, Base):
    """用户操作审计日志"""

    __tablename__ = "user_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="被操作用户ID"
    )
    admin_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, comment="操作管理员ID"
    )
    action = Column(String(50), nullable=False, comment="操作类型")
    old_values = Column(Text, nullable=True, comment="操作前的值(JSON)")
    new_values = Column(Text, nullable=True, comment="操作后的值(JSON)")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="操作时间"
    )

    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")
    admin_user = relationship(
        "User", foreign_keys=[admin_user_id], backref="admin_actions"
    )
