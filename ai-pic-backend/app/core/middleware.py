"""中间件模块

提供用户认证、权限控制、请求日志等中间件
"""
from datetime import datetime
from typing import Optional, Callable
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class UserPermissionLevel:
    """用户权限级别枚举"""
    BASIC_AUTH = "basic_auth"           # 基础认证（仅登录）
    ACTIVE_USER = "active_user"         # 活跃用户（激活+审批）
    ADMIN = "admin"                     # 管理员权限
    SUPERUSER = "superuser"             # 超级用户权限

def get_current_user_basic(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """基础用户认证 - 仅验证token有效性"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user_basic)
) -> User:
    """获取当前活跃用户 - 需要通过审批且账户激活"""
    # 检查账户是否被锁定
    if current_user.is_account_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账户已被锁定，请联系管理员或稍后再试"
        )
    
    # 检查用户是否可以登录
    if not current_user.can_login:
        # 具体的错误信息
        if not current_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="邮箱未验证，请先验证邮箱"
            )
        elif not current_user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户待管理员审批，请耐心等待"
            )
        elif not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被停用，请联系管理员"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户状态异常，请联系管理员"
            )
    
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user

def require_permission(permission_level: str) -> Callable:
    """权限装饰器工厂"""
    permission_functions = {
        UserPermissionLevel.BASIC_AUTH: get_current_user_basic,
        UserPermissionLevel.ACTIVE_USER: get_current_active_user,
        UserPermissionLevel.ADMIN: get_current_admin_user,
        UserPermissionLevel.SUPERUSER: get_current_superuser,
    }
    
    if permission_level not in permission_functions:
        raise ValueError(f"未知的权限级别: {permission_level}")
    
    return permission_functions[permission_level]

# 别名函数，方便使用
def require_basic_auth() -> User:
    """要求基础认证"""
    return Depends(get_current_user_basic)

def require_active_user() -> User:
    """要求活跃用户"""
    return Depends(get_current_active_user)

def require_admin() -> User:
    """要求管理员权限"""
    return Depends(get_current_admin_user)

def require_superuser() -> User:
    """要求超级用户权限"""
    return Depends(get_current_superuser)

def record_user_login(user: User, db: Session, success: bool = True):
    """记录用户登录"""
    if success:
        user.last_login_at = datetime.utcnow()
        user.failed_login_attempts = 0  # 成功登录时重置失败次数
    else:
        user.failed_login_attempts += 1
        # 超过5次失败尝试，锁定账户1小时
        if user.failed_login_attempts >= 5:
            from datetime import timedelta
            user.account_locked_until = datetime.utcnow() + timedelta(hours=1)
    
    db.commit()
    db.refresh(user)