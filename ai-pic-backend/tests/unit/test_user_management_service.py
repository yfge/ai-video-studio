"""用户管理服务单元测试

专注于测试UserManagementService的业务逻辑
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.services.user_management_service import UserManagementService
from app.models.user import User, UserAuditLog
from app.schemas.user import UserApprovalRequest
from fastapi import HTTPException


class TestUserManagementService:
    """用户管理服务测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.db = Mock(spec=Session)
        self.service = UserManagementService(self.db)
    
    def create_mock_user(self, **kwargs):
        """创建模拟用户"""
        defaults = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": False,
            "is_approved": False,
            "email_verified": False,
            "is_admin": False,
            "is_superuser": False,
            "failed_login_attempts": 0,
            "account_locked_until": None,
            "approved_at": None,
            "approved_by_user_id": None,
        }
        defaults.update(kwargs)
        
        user = Mock()
        for key, value in defaults.items():
            setattr(user, key, value)
        
        return user
    
    def create_mock_admin(self, **kwargs):
        """创建模拟管理员用户"""
        defaults = {
            "id": 99,
            "username": "admin",
            "is_admin": True,
            "is_superuser": False,
        }
        defaults.update(kwargs)
        return self.create_mock_user(**defaults)


class TestUserApproval(TestUserManagementService):
    """用户审批测试"""
    
    def test_approve_user_success(self):
        """测试用户审批成功"""
        # 准备
        user = self.create_mock_user()
        admin = self.create_mock_admin()
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        approval_data = UserApprovalRequest(action="approve", reason="Test approval")
        
        # 执行
        result = self.service.approve_user(
            user_id=1,
            admin_user=admin,
            approval_data=approval_data
        )
        
        # 验证
        assert user.is_approved is True
        assert user.is_active is True
        assert user.approved_by_user_id == admin.id
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(user)
    
    def test_reject_user_success(self):
        """测试用户拒绝成功"""
        user = self.create_mock_user()
        admin = self.create_mock_admin()
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        approval_data = UserApprovalRequest(action="reject", reason="Test rejection")
        
        result = self.service.approve_user(
            user_id=1,
            admin_user=admin,
            approval_data=approval_data
        )
        
        assert user.is_approved is False
        assert user.is_active is False
    
    def test_approve_nonexistent_user_fails(self):
        """测试审批不存在用户失败"""
        admin = self.create_mock_admin()
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        approval_data = UserApprovalRequest(action="approve")
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.approve_user(
                user_id=999,
                admin_user=admin,
                approval_data=approval_data
            )
        
        assert exc_info.value.status_code == 404
        assert "用户不存在" in str(exc_info.value.detail)
    
    def test_invalid_approval_action_fails(self):
        """测试无效审批操作失败"""
        user = self.create_mock_user()
        admin = self.create_mock_admin()
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        approval_data = UserApprovalRequest(action="invalid_action")
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.approve_user(
                user_id=1,
                admin_user=admin,
                approval_data=approval_data
            )
        
        assert exc_info.value.status_code == 400
        assert "无效的操作类型" in str(exc_info.value.detail)


class TestRoleManagement(TestUserManagementService):
    """角色管理测试"""
    
    def test_update_user_role_success(self):
        """测试更新用户角色成功"""
        user = self.create_mock_user(id=1)
        admin = self.create_mock_admin(id=2)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.update_user_role(
            user_id=1,
            admin_user=admin,
            is_admin=True,
            is_superuser=False
        )
        
        assert user.is_admin is True
        assert user.is_superuser is False
        self.db.commit.assert_called_once()
    
    def test_cannot_modify_own_permissions(self):
        """测试不能修改自己的权限"""
        user = self.create_mock_user(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.update_user_role(
                user_id=1,
                admin_user=user,  # 同一个用户
                is_admin=False
            )
        
        assert exc_info.value.status_code == 400
        assert "不能修改自己的权限" in str(exc_info.value.detail)


class TestUserSuspension(TestUserManagementService):
    """用户暂停测试"""
    
    def test_suspend_user_success(self):
        """测试暂停用户成功"""
        user = self.create_mock_user(id=1, is_active=True)
        admin = self.create_mock_admin(id=2)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.suspend_user(
            user_id=1,
            admin_user=admin,
            duration_hours=24,
            reason="Test suspension"
        )
        
        assert user.is_active is False
        assert user.account_locked_until is not None
        self.db.commit.assert_called_once()
    
    def test_cannot_suspend_self(self):
        """测试不能暂停自己"""
        user = self.create_mock_user(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.suspend_user(
                user_id=1,
                admin_user=user,  # 同一个用户
                duration_hours=24
            )
        
        assert exc_info.value.status_code == 400
        assert "不能暂停自己的账户" in str(exc_info.value.detail)
    
    def test_reactivate_user_success(self):
        """测试重新激活用户成功"""
        user = self.create_mock_user(
            id=1,
            is_active=False,
            account_locked_until=datetime.utcnow() + timedelta(hours=1),
            failed_login_attempts=3
        )
        admin = self.create_mock_admin(id=2)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.reactivate_user(
            user_id=1,
            admin_user=admin
        )
        
        assert user.is_active is True
        assert user.account_locked_until is None
        assert user.failed_login_attempts == 0


class TestUserDeletion(TestUserManagementService):
    """用户删除测试"""
    
    def test_delete_user_success(self):
        """测试删除用户成功"""
        user = self.create_mock_user(id=1)
        admin = self.create_mock_admin(id=2)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.delete_user(
            user_id=1,
            admin_user=admin
        )
        
        assert result is True
        self.db.delete.assert_called_once_with(user)
        self.db.commit.assert_called_once()
    
    def test_cannot_delete_self(self):
        """测试不能删除自己"""
        user = self.create_mock_user(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.delete_user(
                user_id=1,
                admin_user=user  # 同一个用户
            )
        
        assert exc_info.value.status_code == 400
        assert "不能删除自己的账户" in str(exc_info.value.detail)


class TestUserStats(TestUserManagementService):
    """用户统计测试"""
    
    def test_get_user_stats_success(self):
        """测试获取用户统计成功"""
        # 模拟数据库查询结果
        self.db.query.return_value.count.side_effect = [
            10,  # total_users
            8,   # active_users
            2,   # pending_approval
            2,   # suspended_users
            1,   # admin_users
            3    # recent_registrations
        ]
        
        stats = self.service.get_user_stats()
        
        assert stats.total_users == 10
        assert stats.active_users == 8
        assert stats.pending_approval == 2
        assert stats.suspended_users == 2
        assert stats.admin_users == 1
        assert stats.recent_registrations == 3


class TestActivationToken(TestUserManagementService):
    """激活令牌测试"""
    
    @patch('app.services.user_management_service.uuid')
    def test_generate_activation_token_success(self, mock_uuid):
        """测试生成激活令牌成功"""
        mock_uuid.uuid4.return_value = "test-token-123"
        user = self.create_mock_user()
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        token = self.service.generate_activation_token(user_id=1)
        
        assert token == "test-token-123"
        assert user.activation_token == "test-token-123"
        assert user.activation_token_expires is not None
        self.db.commit.assert_called_once()
    
    def test_verify_activation_token_success(self):
        """测试验证激活令牌成功"""
        user = self.create_mock_user(
            activation_token="valid-token",
            activation_token_expires=datetime.utcnow() + timedelta(hours=1)
        )
        query_mock = self.db.query.return_value.filter.return_value.first
        query_mock.return_value = user
        
        result = self.service.verify_activation_token("valid-token")
        
        assert result == user
        assert user.email_verified is True
        assert user.activation_token is None
        assert user.activation_token_expires is None
    
    def test_verify_expired_token_fails(self):
        """测试验证过期令牌失败"""
        query_mock = self.db.query.return_value.filter.return_value.first
        query_mock.return_value = None  # 模拟找不到有效令牌
        
        result = self.service.verify_activation_token("expired-token")
        
        assert result is None


class TestLoginAttempts(TestUserManagementService):
    """登录尝试测试"""
    
    def test_reset_failed_login_attempts(self):
        """测试重置失败登录次数"""
        user = self.create_mock_user(
            failed_login_attempts=3,
            account_locked_until=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.reset_failed_login_attempts(user_id=1)
        
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None
        self.db.commit.assert_called_once()
    
    def test_increment_failed_login_attempts(self):
        """测试增加失败登录次数"""
        user = self.create_mock_user(failed_login_attempts=2)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.increment_failed_login_attempts(user_id=1)
        
        assert user.failed_login_attempts == 3
        self.db.commit.assert_called_once()
    
    def test_lock_account_after_five_failures(self):
        """测试5次失败后锁定账户"""
        user = self.create_mock_user(failed_login_attempts=4)
        self.db.query.return_value.filter.return_value.first.return_value = user
        
        result = self.service.increment_failed_login_attempts(user_id=1)
        
        assert user.failed_login_attempts == 5
        assert user.account_locked_until is not None


class TestAuditLog(TestUserManagementService):
    """审计日志测试"""
    
    def test_create_audit_log_success(self):
        """测试创建审计日志成功"""
        old_values = {"is_active": False}
        new_values = {"is_active": True}
        
        audit_log = self.service._create_audit_log(
            user_id=1,
            admin_user_id=2,
            action="USER_ACTIVATED",
            old_values=old_values,
            new_values=new_values,
            ip_address="192.168.1.1",
            user_agent="TestAgent"
        )
        
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()
    
    def test_get_user_audit_logs(self):
        """测试获取用户审计日志"""
        mock_logs = [Mock(), Mock()]
        query_mock = self.db.query.return_value.filter.return_value
        query_mock.count.return_value = 2
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_logs
        
        logs, total = self.service.get_user_audit_logs(user_id=1, page=1, size=10)
        
        assert len(logs) == 2
        assert total == 2


class TestUserSearch(TestUserManagementService):
    """用户搜索测试"""
    
    def test_get_users_list_with_filters(self):
        """测试带筛选条件的用户列表"""
        mock_users = [Mock(), Mock()]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value = query_mock  # 链式调用
        query_mock.count.return_value = 2
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        users, total = self.service.get_users_list(
            page=1,
            size=10,
            status_filter="pending",
            role_filter="admin",
            search="test"
        )
        
        assert len(users) == 2
        assert total == 2
        # 验证过滤器被应用（具体的filter调用次数取决于实现）
        assert query_mock.filter.call_count >= 1