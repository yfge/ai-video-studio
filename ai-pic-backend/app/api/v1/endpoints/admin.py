"""管理员API端点

提供用户管理、系统管理等管理员功能
"""

import math
from typing import List, Optional

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    UserAdminResponse,
    UserAdminUpdate,
    UserApprovalRequest,
    UserAuditLogResponse,
    UserListResponse,
    UserStatsResponse,
)
from app.services.user_management_service import UserManagementService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

router = APIRouter()


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return current_user


def get_client_info(request: Request) -> tuple:
    """获取客户端信息"""
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.get("/users", response_model=UserListResponse)
def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(
        None, description="状态筛选: pending, approved, suspended, locked"
    ),
    role_filter: Optional[str] = Query(
        None, description="角色筛选: admin, superuser, user"
    ),
    search: Optional[str] = Query(None, description="搜索用户名、邮箱或姓名"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取用户列表"""
    service = UserManagementService(db)
    users, total = service.get_users_list(
        page=page,
        size=size,
        status_filter=status_filter,
        role_filter=role_filter,
        search=search,
    )

    pages = math.ceil(total / size)

    return UserListResponse(users=users, total=total, page=page, size=size, pages=pages)


@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取用户详情"""
    user = _not_deleted(db.query(User), User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/users/{user_id}/approval", response_model=UserAdminResponse)
def approve_or_reject_user(
    user_id: int,
    approval_data: UserApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """审批或拒绝用户"""
    service = UserManagementService(db)
    ip_address, user_agent = get_client_info(request)

    user = service.approve_user(
        user_id=user_id,
        admin_user=current_user,
        approval_data=approval_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return user


@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
def update_user_role(
    user_id: int,
    is_admin: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """更新用户角色"""
    # 只有超级用户才能设置管理员权限
    if is_superuser is not None and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级用户才能设置超级用户权限",
        )

    service = UserManagementService(db)
    ip_address, user_agent = get_client_info(request)

    user = service.update_user_role(
        user_id=user_id,
        admin_user=current_user,
        is_admin=is_admin,
        is_superuser=is_superuser,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return user


@router.put("/users/{user_id}/suspend", response_model=UserAdminResponse)
def suspend_user(
    user_id: int,
    duration_hours: Optional[int] = Query(
        None, description="暂停时长（小时），不设置则永久暂停"
    ),
    reason: Optional[str] = Query(None, description="暂停原因"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """暂停用户"""
    service = UserManagementService(db)
    ip_address, user_agent = get_client_info(request)

    user = service.suspend_user(
        user_id=user_id,
        admin_user=current_user,
        duration_hours=duration_hours,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return user


@router.put("/users/{user_id}/reactivate", response_model=UserAdminResponse)
def reactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """重新激活用户"""
    service = UserManagementService(db)
    ip_address, user_agent = get_client_info(request)

    user = service.reactivate_user(
        user_id=user_id,
        admin_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """删除用户"""
    # 只有超级用户才能删除用户
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="只有超级用户才能删除用户"
        )

    service = UserManagementService(db)
    ip_address, user_agent = get_client_info(request)

    success = service.delete_user(
        user_id=user_id,
        admin_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {"message": "用户已删除", "success": success}


@router.get("/users/{user_id}/audit-logs", response_model=List[UserAuditLogResponse])
def get_user_audit_logs(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取用户审计日志"""
    service = UserManagementService(db)
    logs, total = service.get_user_audit_logs(user_id, page, size)
    return logs


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """获取用户统计信息"""
    service = UserManagementService(db)
    return service.get_user_stats()


@router.post("/users/{user_id}/reset-login-attempts", response_model=UserAdminResponse)
def reset_user_login_attempts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """重置用户失败登录次数"""
    service = UserManagementService(db)
    user = service.reset_failed_login_attempts(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/users/{user_id}/generate-activation-token")
def generate_user_activation_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """生成用户激活令牌"""
    service = UserManagementService(db)
    token = service.generate_activation_token(user_id)
    return {"activation_token": token, "message": "激活令牌已生成"}


@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user_admin(
    user_id: int,
    user_update: UserAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """管理员更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 记录旧值
    old_values = {}
    new_values = {}

    # 更新字段
    update_fields = user_update.dict(exclude_unset=True)
    for field, value in update_fields.items():
        if hasattr(user, field):
            old_values[field] = getattr(user, field)
            setattr(user, field, value)
            new_values[field] = value

    # 记录审计日志
    if old_values:
        service = UserManagementService(db)
        ip_address, user_agent = get_client_info(request)
        service._create_audit_log(
            user_id=user_id,
            admin_user_id=current_user.id,
            action="USER_UPDATED",
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    db.commit()
    db.refresh(user)

    return user
