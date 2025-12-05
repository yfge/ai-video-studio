"""用户管理系统测试

全面测试用户注册、审批、权限管理等功能
"""
import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.user import User, UserAuditLog
from app.core.security import get_password_hash, create_access_token
from tests.conftest import override_get_db

# 全局测试客户端，使用测试数据库覆盖
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestUserRegistration:
    """用户注册测试"""
    
    def test_register_creates_inactive_user(self, db_session: Session, client):
        """测试注册创建未激活用户"""
        # 首用户创建管理员，先清理
        db_session.query(User).delete()
        db_session.commit()

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"
        # 首个用户自动晋升为管理员并激活
        assert data["is_active"] is True
        assert data["is_approved"] is True
        assert data["email_verified"] is True
        assert data["is_admin"] is True
        assert data["is_superuser"] is True

    def test_register_subsequent_user_is_pending(self, db_session: Session, client):
        """测试第二个用户保持待审批状态"""
        db_session.query(User).delete()
        db_session.commit()

        # 首个用户 -> 管理员
        client.post("/api/v1/auth/register", json={
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "pass123",
        })

        # 第二个用户
        response = client.post("/api/v1/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "pass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["is_approved"] is False
        assert data["email_verified"] is False
        assert data["is_admin"] is False
        assert data["is_superuser"] is False
    
    def test_register_duplicate_username(self, db_session: Session, client):
        """测试重复用户名注册"""
        db_session.query(User).delete()
        db_session.commit()
        # 创建第一个用户
        user1_data = {
            "username": "duplicate",
            "email": "user1@example.com",
            "password": "pass123",
        }
        client.post("/api/v1/auth/register", json=user1_data)
        
        # 尝试用相同用户名创建第二个用户
        user2_data = {
            "username": "duplicate",
            "email": "user2@example.com",
            "password": "pass123",
        }
        
        response = client.post("/api/v1/auth/register", json=user2_data)
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]
    
    def test_register_duplicate_email(self, db_session: Session, client):
        """测试重复邮箱注册"""
        db_session.query(User).delete()
        db_session.commit()
        user1_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "pass123",
        }
        client.post("/api/v1/auth/register", json=user1_data)
        
        user2_data = {
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "pass123",
        }
        
        response = client.post("/api/v1/auth/register", json=user2_data)
        assert response.status_code == 400
        assert "邮箱已存在" in response.json()["detail"]


class TestUserLogin:
    """用户登录测试"""
    
    def create_approved_user(self, db: Session, username: str = "activeuser"):
        """创建已审批的测试用户"""
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            is_approved=True,
            email_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def create_pending_user(self, db: Session, username: str = "pendinguser"):
        """创建待审批的测试用户"""
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=False,
            is_approved=False,
            email_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def test_login_approved_user_success(self, db: Session):
        """测试已审批用户登录成功"""
        user = self.create_approved_user(db)
        
        response = client.post("/api/v1/auth/login", data={
            "username": user.username,
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_pending_user_fails(self, db: Session):
        """测试待审批用户登录失败"""
        user = self.create_pending_user(db)
        
        response = client.post("/api/v1/auth/login", data={
            "username": user.username,
            "password": "testpass123"
        })
        
        assert response.status_code == 403
        assert "邮箱" in response.json()["detail"] or "审批" in response.json()["detail"]
    
    def test_login_invalid_credentials(self, db: Session):
        """测试错误凭证登录"""
        user = self.create_approved_user(db)
        
        response = client.post("/api/v1/auth/login", data={
            "username": user.username,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_login_increments_failed_attempts(self, db: Session):
        """测试失败登录增加失败次数"""
        user = self.create_approved_user(db)
        
        # 连续失败登录
        for i in range(3):
            client.post("/api/v1/auth/login", data={
                "username": user.username,
                "password": "wrongpassword"
            })
        
        db.refresh(user)
        assert user.failed_login_attempts == 3
    
    def test_account_locks_after_five_failures(self, db: Session):
        """测试5次失败后账户锁定"""
        user = self.create_approved_user(db)
        
        # 连续5次失败登录
        for i in range(5):
            client.post("/api/v1/auth/login", data={
                "username": user.username,
                "password": "wrongpassword"
            })
        
        db.refresh(user)
        assert user.failed_login_attempts == 5
        assert user.account_locked_until is not None
        assert user.account_locked_until > datetime.utcnow()


class TestUserManagementService:
    """用户管理服务测试"""
    
    def create_admin_user(self, db: Session):
        """创建管理员用户"""
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass"),
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    def create_test_user(self, db: Session, username: str = "testuser"):
        """创建测试用户"""
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=False,
            is_approved=False,
            email_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def test_approve_user_success(self, db: Session):
        """测试用户审批成功"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        from app.schemas.user import UserApprovalRequest
        approval_data = UserApprovalRequest(action="approve", reason="Test approval")
        
        result = service.approve_user(
            user_id=user.id,
            admin_user=admin,
            approval_data=approval_data
        )
        
        assert result.is_approved is True
        assert result.is_active is True
        assert result.approved_at is not None
        assert result.approved_by_user_id == admin.id
    
    def test_reject_user_success(self, db: Session):
        """测试用户拒绝成功"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        from app.schemas.user import UserApprovalRequest
        approval_data = UserApprovalRequest(action="reject", reason="Test rejection")
        
        result = service.approve_user(
            user_id=user.id,
            admin_user=admin,
            approval_data=approval_data
        )
        
        assert result.is_approved is False
        assert result.is_active is False
    
    def test_update_user_role(self, db: Session):
        """测试更新用户角色"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        result = service.update_user_role(
            user_id=user.id,
            admin_user=admin,
            is_admin=True
        )
        
        assert result.is_admin is True
    
    def test_suspend_user(self, db: Session):
        """测试暂停用户"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        result = service.suspend_user(
            user_id=user.id,
            admin_user=admin,
            duration_hours=24,
            reason="Test suspension"
        )
        
        assert result.is_active is False
        assert result.account_locked_until is not None
    
    def test_reactivate_user(self, db: Session):
        """测试重新激活用户"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        # 先暂停用户
        service.suspend_user(user_id=user.id, admin_user=admin)
        
        # 再重新激活
        result = service.reactivate_user(
            user_id=user.id,
            admin_user=admin
        )
        
        assert result.is_active is True
        assert result.account_locked_until is None
        assert result.failed_login_attempts == 0
    
    def test_get_user_stats(self, db: Session):
        """测试获取用户统计"""
        # 创建不同状态的用户
        admin = self.create_admin_user(db)
        
        # 创建几个不同状态的用户用于统计
        for i in range(3):
            user = User(
                username=f"active_user_{i}",
                email=f"active_{i}@example.com",
                hashed_password=get_password_hash("pass"),
                is_active=True,
                is_approved=True,
                email_verified=True
            )
            db.add(user)
        
        for i in range(2):
            user = User(
                username=f"pending_user_{i}",
                email=f"pending_{i}@example.com",
                hashed_password=get_password_hash("pass"),
                is_active=False,
                is_approved=False,
                email_verified=False
            )
            db.add(user)
        
        db.commit()
        
        service = UserManagementService(db)
        stats = service.get_user_stats()
        
        assert stats.total_users >= 6  # admin + 3 active + 2 pending
        assert stats.active_users >= 4  # admin + 3 active
        assert stats.pending_approval >= 2
        assert stats.admin_users >= 1
    
    def test_audit_log_creation(self, db: Session):
        """测试审计日志创建"""
        admin = self.create_admin_user(db)
        user = self.create_test_user(db)
        service = UserManagementService(db)
        
        from app.schemas.user import UserApprovalRequest
        approval_data = UserApprovalRequest(action="approve", reason="Test")
        
        service.approve_user(
            user_id=user.id,
            admin_user=admin,
            approval_data=approval_data,
            ip_address="127.0.0.1",
            user_agent="TestClient"
        )
        
        # 检查审计日志
        audit_log = db.query(UserAuditLog).filter(
            UserAuditLog.user_id == user.id,
            UserAuditLog.action == "USER_APPROVED"
        ).first()
        
        assert audit_log is not None
        assert audit_log.admin_user_id == admin.id
        assert audit_log.ip_address == "127.0.0.1"
        assert audit_log.user_agent == "TestClient"
        assert audit_log.old_values is not None
        assert audit_log.new_values is not None


class TestAdminAPI:
    """管理员API测试"""
    
    def create_admin_user(self, db: Session):
        """创建管理员用户"""
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass"),
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    def create_regular_user(self, db: Session):
        """创建普通用户"""
        user = User(
            username="regularuser",
            email="regular@example.com",
            hashed_password=get_password_hash("userpass"),
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def get_admin_token(self, admin_user: User) -> str:
        """获取管理员token"""
        return create_access_token(data={"sub": admin_user.username})
    
    def test_admin_can_access_user_list(self, db: Session):
        """测试管理员可以访问用户列表"""
        admin = self.create_admin_user(db)
        token = self.get_admin_token(admin)
        
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
    
    def test_regular_user_cannot_access_admin_endpoints(self, db: Session):
        """测试普通用户无法访问管理员接口"""
        user = self.create_regular_user(db)
        token = self.get_admin_token(user)
        
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "管理员权限" in response.json()["detail"]
    
    def test_admin_can_approve_user(self, db: Session):
        """测试管理员可以审批用户"""
        admin = self.create_admin_user(db)
        token = self.get_admin_token(admin)
        
        # 创建待审批用户
        pending_user = User(
            username="pending",
            email="pending@example.com",
            hashed_password=get_password_hash("pass"),
            is_active=False,
            is_approved=False,
            email_verified=True
        )
        db.add(pending_user)
        db.commit()
        db.refresh(pending_user)
        
        response = client.put(
            f"/api/v1/admin/users/{pending_user.id}/approval",
            headers={"Authorization": f"Bearer {token}"},
            json={"action": "approve", "reason": "Test approval"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_approved"] is True
        assert data["is_active"] is True
    
    def test_admin_can_get_user_stats(self, db: Session):
        """测试管理员可以获取用户统计"""
        admin = self.create_admin_user(db)
        token = self.get_admin_token(admin)
        
        response = client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "pending_approval" in data
        assert "admin_users" in data
    
    def test_admin_can_suspend_user(self, db: Session):
        """测试管理员可以暂停用户"""
        admin = self.create_admin_user(db)
        user = self.create_regular_user(db)
        token = self.get_admin_token(admin)
        
        response = client.put(
            f"/api/v1/admin/users/{user.id}/suspend",
            headers={"Authorization": f"Bearer {token}"},
            params={"duration_hours": 24, "reason": "Test suspension"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestEmailVerification:
    """邮箱验证测试"""
    
    def test_generate_activation_token(self, db: Session):
        """测试生成激活令牌"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            email_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        service = UserManagementService(db)
        token = service.generate_activation_token(user.id)
        
        assert token is not None
        db.refresh(user)
        assert user.activation_token == token
        assert user.activation_token_expires is not None
    
    def test_verify_activation_token_success(self, db: Session):
        """测试验证激活令牌成功"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            email_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        service = UserManagementService(db)
        token = service.generate_activation_token(user.id)
        
        result = service.verify_activation_token(token)
        
        assert result is not None
        assert result.email_verified is True
        assert result.activation_token is None
    
    def test_verify_expired_token_fails(self, db: Session):
        """测试验证过期令牌失败"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            email_verified=False,
            activation_token="expired_token",
            activation_token_expires=datetime.utcnow() - timedelta(hours=1)
        )
        db.add(user)
        db.commit()
        
        service = UserManagementService(db)
        result = service.verify_activation_token("expired_token")
        
        assert result is None


class TestMiddleware:
    """中间件测试"""
    
    def test_require_active_user_blocks_inactive(self, db: Session):
        """测试活跃用户中间件阻止非活跃用户"""
        # 创建未激活用户
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("pass"),
            is_active=False,
            is_approved=False,
            email_verified=False
        )
        db.add(user)
        db.commit()
        
        token = create_access_token(data={"sub": user.username})
        
        # 尝试访问需要活跃用户权限的接口
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "审批" in response.json()["detail"] or "验证" in response.json()["detail"]
    
    def test_require_admin_blocks_regular_user(self, db: Session):
        """测试管理员中间件阻止普通用户"""
        user = User(
            username="regular",
            email="regular@example.com",
            hashed_password=get_password_hash("pass"),
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=False
        )
        db.add(user)
        db.commit()
        
        token = create_access_token(data={"sub": user.username})
        
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "管理员权限" in response.json()["detail"]
