"""用户管理服务

提供用户激活、审批、角色管理等核心业务逻辑
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status

from app.models.user import User, UserAuditLog
from app.schemas.user import UserAdminUpdate, UserApprovalRequest, UserStatsResponse
from app.core.security import get_password_hash


class UserManagementService:
    """用户管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_users_list(
        self, 
        page: int = 1, 
        size: int = 20,
        status_filter: Optional[str] = None,
        role_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """获取用户列表"""
        query = self.db.query(User)
        
        # 状态筛选
        if status_filter == "pending":
            query = query.filter(and_(User.is_active == False, User.is_approved == False))
        elif status_filter == "approved":
            query = query.filter(User.is_approved == True)
        elif status_filter == "suspended":
            query = query.filter(User.is_active == False)
        elif status_filter == "locked":
            query = query.filter(User.account_locked_until > datetime.utcnow())
        
        # 角色筛选
        if role_filter == "admin":
            query = query.filter(User.is_admin == True)
        elif role_filter == "superuser":
            query = query.filter(User.is_superuser == True)
        elif role_filter == "user":
            query = query.filter(and_(User.is_admin == False, User.is_superuser == False))
        
        # 搜索
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            ))
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * size
        users = query.order_by(desc(User.created_at)).offset(offset).limit(size).all()
        
        return users, total
    
    def approve_user(
        self, 
        user_id: int, 
        admin_user: User, 
        approval_data: UserApprovalRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """审批用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_values = {
            "is_approved": user.is_approved,
            "is_active": user.is_active,
            "approved_at": user.approved_at,
            "approved_by_user_id": user.approved_by_user_id
        }
        
        if approval_data.action == "approve":
            user.is_approved = True
            user.is_active = True
            user.approved_at = datetime.utcnow()
            user.approved_by_user_id = admin_user.id
            action = "USER_APPROVED"
        elif approval_data.action == "reject":
            user.is_approved = False
            user.is_active = False
            action = "USER_REJECTED"
        else:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        new_values = {
            "is_approved": user.is_approved,
            "is_active": user.is_active,
            "approved_at": user.approved_at,
            "approved_by_user_id": user.approved_by_user_id,
            "reason": approval_data.reason
        }
        
        # 记录审计日志
        self._create_audit_log(
            user_id=user_id,
            admin_user_id=admin_user.id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user_role(
        self, 
        user_id: int, 
        admin_user: User,
        is_admin: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """更新用户角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 防止降级自己的权限
        if user.id == admin_user.id:
            raise HTTPException(status_code=400, detail="不能修改自己的权限")
        
        old_values = {
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser
        }
        
        if is_admin is not None:
            user.is_admin = is_admin
        if is_superuser is not None:
            user.is_superuser = is_superuser
        
        new_values = {
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser
        }
        
        # 记录审计日志
        self._create_audit_log(
            user_id=user_id,
            admin_user_id=admin_user.id,
            action="ROLE_UPDATED",
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def suspend_user(
        self, 
        user_id: int, 
        admin_user: User,
        duration_hours: Optional[int] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """暂停用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 防止暂停自己
        if user.id == admin_user.id:
            raise HTTPException(status_code=400, detail="不能暂停自己的账户")
        
        old_values = {
            "is_active": user.is_active,
            "account_locked_until": user.account_locked_until
        }
        
        user.is_active = False
        if duration_hours:
            user.account_locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
        
        new_values = {
            "is_active": user.is_active,
            "account_locked_until": user.account_locked_until,
            "reason": reason,
            "duration_hours": duration_hours
        }
        
        # 记录审计日志
        self._create_audit_log(
            user_id=user_id,
            admin_user_id=admin_user.id,
            action="USER_SUSPENDED",
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def reactivate_user(
        self, 
        user_id: int, 
        admin_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """重新激活用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_values = {
            "is_active": user.is_active,
            "account_locked_until": user.account_locked_until,
            "failed_login_attempts": user.failed_login_attempts
        }
        
        user.is_active = True
        user.account_locked_until = None
        user.failed_login_attempts = 0
        
        new_values = {
            "is_active": user.is_active,
            "account_locked_until": user.account_locked_until,
            "failed_login_attempts": user.failed_login_attempts
        }
        
        # 记录审计日志
        self._create_audit_log(
            user_id=user_id,
            admin_user_id=admin_user.id,
            action="USER_REACTIVATED",
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(
        self, 
        user_id: int, 
        admin_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """删除用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 防止删除自己
        if user.id == admin_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")
        
        # 记录删除前的用户信息
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        
        # 记录审计日志
        self._create_audit_log(
            user_id=user_id,
            admin_user_id=admin_user.id,
            action="USER_DELETED",
            old_values=user_info,
            new_values=None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.delete(user)
        self.db.commit()
        
        return True
    
    def get_user_stats(self) -> UserStatsResponse:
        """获取用户统计信息"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        pending_approval = self.db.query(User).filter(
            and_(User.is_approved == False, User.is_active == False)
        ).count()
        suspended_users = self.db.query(User).filter(User.is_active == False).count()
        admin_users = self.db.query(User).filter(User.is_admin == True).count()
        
        # 最近7天注册用户数
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = self.db.query(User).filter(
            User.created_at >= seven_days_ago
        ).count()
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            pending_approval=pending_approval,
            suspended_users=suspended_users,
            admin_users=admin_users,
            recent_registrations=recent_registrations
        )
    
    def generate_activation_token(self, user_id: int) -> str:
        """生成用户激活令牌"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        token = str(uuid.uuid4())
        user.activation_token = token
        user.activation_token_expires = datetime.utcnow() + timedelta(hours=24)
        
        self.db.commit()
        
        return token
    
    def verify_activation_token(self, token: str) -> Optional[User]:
        """验证激活令牌"""
        user = self.db.query(User).filter(
            and_(
                User.activation_token == token,
                User.activation_token_expires > datetime.utcnow()
            )
        ).first()
        
        if user:
            user.email_verified = True
            user.activation_token = None
            user.activation_token_expires = None
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def reset_failed_login_attempts(self, user_id: int) -> User:
        """重置失败登录次数"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.failed_login_attempts = 0
            user.account_locked_until = None
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def increment_failed_login_attempts(self, user_id: int) -> User:
        """增加失败登录次数"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.failed_login_attempts += 1
            # 超过5次失败尝试，锁定账户1小时
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(hours=1)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def _create_audit_log(
        self,
        user_id: int,
        admin_user_id: Optional[int],
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserAuditLog:
        """创建审计日志"""
        audit_log = UserAuditLog(
            user_id=user_id,
            admin_user_id=admin_user_id,
            action=action,
            old_values=json.dumps(old_values, default=str) if old_values else None,
            new_values=json.dumps(new_values, default=str) if new_values else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        self.db.flush()  # 确保ID被分配但不提交事务
        
        return audit_log
    
    def get_user_audit_logs(
        self, 
        user_id: int, 
        page: int = 1, 
        size: int = 20
    ) -> Tuple[List[UserAuditLog], int]:
        """获取用户审计日志"""
        query = self.db.query(UserAuditLog).filter(UserAuditLog.user_id == user_id)
        total = query.count()
        
        offset = (page - 1) * size
        logs = query.order_by(desc(UserAuditLog.created_at)).offset(offset).limit(size).all()
        
        return logs, total