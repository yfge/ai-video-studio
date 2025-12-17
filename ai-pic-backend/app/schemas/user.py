from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin" 
    SUPERUSER = "superuser"

class UserStatus(str, Enum):
    PENDING = "pending"           # 待审批
    APPROVED = "approved"         # 已审批
    REJECTED = "rejected"         # 已拒绝
    SUSPENDED = "suspended"       # 已暂停

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    language: Optional[str] = "zh-CN"
    timezone: Optional[str] = "Asia/Shanghai"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None

class UserAdminUpdate(BaseModel):
    """管理员更新用户信息"""
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_approved: Optional[bool] = None
    email_verified: Optional[bool] = None
    failed_login_attempts: Optional[int] = None
    account_locked_until: Optional[datetime] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    business_id: str
    is_active: bool
    is_superuser: bool
    is_admin: bool
    is_approved: bool
    email_verified: bool
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int
    is_account_locked: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserAdminResponse(UserResponse):
    """管理员查看用户详细信息"""
    approved_at: Optional[datetime] = None
    approved_by_user_id: Optional[int] = None
    activation_token_expires: Optional[datetime] = None
    account_locked_until: Optional[datetime] = None
    
class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserAdminResponse]
    total: int
    page: int
    size: int
    pages: int

class UserStatsResponse(BaseModel):
    """用户统计信息"""
    total_users: int
    active_users: int
    pending_approval: int
    suspended_users: int
    admin_users: int
    recent_registrations: int  # 最近7天注册

class UserApprovalRequest(BaseModel):
    """用户审批请求"""
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserAuditLogResponse(BaseModel):
    """用户审计日志响应"""
    id: int
    user_id: int
    admin_user_id: Optional[int] = None
    action: str
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 
