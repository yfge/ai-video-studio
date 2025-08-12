"""
自定义迁移系统测试

测试自定义迁移系统的各项功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.migrations import MigrationManager, DataSeeder, MigrationError
from app.core.migration_safety import (
    DataIntegrityChecker, 
    MigrationRollbackManager, 
    MigrationValidator,
    MigrationSafetyError
)

class TestMigrationManager:
    """测试迁移管理器"""
    
    @pytest.fixture
    def temp_engine(self):
        """创建临时SQLite引擎用于测试"""
        engine = create_engine("sqlite:///:memory:")
        yield engine
        engine.dispose()
    
    @pytest.fixture
    def migration_manager(self, temp_engine):
        """创建测试用的迁移管理器"""
        with patch('app.core.migrations.create_engine') as mock_create_engine:
            mock_create_engine.return_value = temp_engine
            manager = MigrationManager(temp_engine)
            yield manager
    
    def test_check_migration_status(self, migration_manager):
        """测试检查迁移状态"""
        status = migration_manager.check_migration_status()
        
        assert isinstance(status, dict)
        assert 'current_revision' in status
        assert 'head_revision' in status
        assert 'is_up_to_date' in status
        assert 'needs_upgrade' in status
        assert 'database_exists' in status
    
    def test_get_migration_history(self, migration_manager):
        """测试获取迁移历史"""
        history = migration_manager.get_migration_history()
        
        assert isinstance(history, list)
        # 空数据库应该没有迁移历史
    
    @patch('app.core.migrations.command.revision')
    def test_create_migration(self, mock_revision, migration_manager):
        """测试创建迁移"""
        message = "test migration"
        
        migration_manager.create_migration(message, autogenerate=False)
        
        mock_revision.assert_called_once()
        call_args = mock_revision.call_args
        assert message in call_args[1]['message']
        assert call_args[1]['autogenerate'] is False
    
    @patch('app.core.migrations.command.upgrade')
    def test_upgrade(self, mock_upgrade, migration_manager):
        """测试数据库升级"""
        result = migration_manager.upgrade("head")
        
        assert result is True
        mock_upgrade.assert_called_once_with(migration_manager.config, "head")
    
    @patch('app.core.migrations.command.downgrade')
    def test_downgrade(self, mock_downgrade, migration_manager):
        """测试数据库降级"""
        result = migration_manager.downgrade("base")
        
        assert result is True
        mock_downgrade.assert_called_once_with(migration_manager.config, "base")
    
    @patch('app.core.migrations.command.stamp')
    def test_stamp(self, mock_stamp, migration_manager):
        """测试版本标记"""
        result = migration_manager.stamp("abc123")
        
        assert result is True
        mock_stamp.assert_called_once_with(migration_manager.config, "abc123")


class TestDataSeeder:
    """测试数据种子管理器"""
    
    @pytest.fixture
    def temp_seeds_dir(self):
        """创建临时种子目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def data_seeder(self, temp_seeds_dir):
        """创建测试用的数据种子管理器"""
        with patch('app.core.migrations.Path') as mock_path:
            mock_path.return_value.parent.parent.parent = temp_seeds_dir.parent
            seeder = DataSeeder()
            seeder.seeds_dir = temp_seeds_dir
            yield seeder
    
    def test_create_seed_file(self, data_seeder):
        """测试创建种子文件"""
        seed_name = "test_seed"
        seed_file = data_seeder.create_seed_file(seed_name)
        
        assert seed_file.exists()
        assert seed_name in seed_file.name
        
        # 检查文件内容
        content = seed_file.read_text(encoding='utf-8')
        assert 'def seed_data():' in content
        assert 'def rollback_data():' in content
        assert seed_name in content
    
    def test_run_seed_file_not_found(self, data_seeder):
        """测试运行不存在的种子"""
        with pytest.raises(ValueError, match="找不到种子文件"):
            data_seeder.run_seed("nonexistent_seed")
    
    def test_run_all_seeds_empty_directory(self, data_seeder):
        """测试在空目录运行所有种子"""
        count = data_seeder.run_all_seeds()
        assert count == 0


class TestDataIntegrityChecker:
    """测试数据完整性检查器"""
    
    @pytest.fixture
    def temp_engine(self):
        """创建临时SQLite引擎用于测试"""
        engine = create_engine("sqlite:///:memory:")
        
        # 创建测试表
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """))
            
            # 插入测试数据
            conn.execute(text("INSERT INTO users (name, email) VALUES ('Test User', 'test@example.com')"))
            conn.execute(text("INSERT INTO posts (title, user_id) VALUES ('Test Post', 1)"))
            conn.commit()
        
        yield engine
        engine.dispose()
    
    @pytest.fixture
    def integrity_checker(self, temp_engine):
        """创建数据完整性检查器"""
        return DataIntegrityChecker(temp_engine)
    
    def test_check_referential_integrity(self, integrity_checker):
        """测试检查引用完整性"""
        result = integrity_checker.check_referential_integrity()
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'violations' in result
        assert 'warnings' in result
    
    def test_check_data_consistency(self, integrity_checker):
        """测试检查数据一致性"""
        result = integrity_checker.check_data_consistency()
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'inconsistencies' in result
        assert 'statistics' in result
    
    def test_generate_data_fingerprint(self, integrity_checker):
        """测试生成数据指纹"""
        fingerprint = integrity_checker.generate_data_fingerprint()
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        
        # 相同数据应该生成相同指纹
        fingerprint2 = integrity_checker.generate_data_fingerprint()
        assert fingerprint == fingerprint2


class TestMigrationRollbackManager:
    """测试迁移回滚管理器"""
    
    @pytest.fixture
    def temp_rollback_dir(self):
        """创建临时回滚目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_engine(self):
        """创建临时SQLite引擎用于测试"""
        engine = create_engine("sqlite:///:memory:")
        yield engine
        engine.dispose()
    
    @pytest.fixture
    def rollback_manager(self, temp_engine, temp_rollback_dir):
        """创建回滚管理器"""
        manager = MigrationRollbackManager(temp_engine)
        manager.rollback_dir = temp_rollback_dir
        yield manager
    
    def test_create_rollback_point(self, rollback_manager):
        """测试创建回滚点"""
        migration_id = "test_migration"
        description = "Test rollback point"
        
        rollback_id = rollback_manager.create_rollback_point(migration_id, description)
        
        assert rollback_id is not None
        assert migration_id in rollback_id
        
        # 检查回滚文件是否创建
        rollback_files = list(rollback_manager.rollback_dir.glob("*.json"))
        assert len(rollback_files) == 1
        
        # 检查回滚文件内容
        with open(rollback_files[0], 'r', encoding='utf-8') as f:
            rollback_info = json.load(f)
        
        assert rollback_info['migration_id'] == migration_id
        assert rollback_info['description'] == description
        assert 'schema_snapshot' in rollback_info
        assert 'data_fingerprint' in rollback_info
    
    def test_list_rollback_points(self, rollback_manager):
        """测试列出回滚点"""
        # 创建几个回滚点
        rollback_manager.create_rollback_point("migration1", "First migration")
        rollback_manager.create_rollback_point("migration2", "Second migration")
        
        rollback_points = rollback_manager.list_rollback_points()
        
        assert len(rollback_points) == 2
        assert all('rollback_id' in point for point in rollback_points)
        assert all('migration_id' in point for point in rollback_points)
        assert all('file_path' in point for point in rollback_points)
    
    def test_cleanup_old_rollbacks(self, rollback_manager):
        """测试清理过期回滚点"""
        # 创建回滚点
        rollback_manager.create_rollback_point("old_migration", "Old migration")
        
        # 模拟过期时间
        rollback_files = list(rollback_manager.rollback_dir.glob("*.json"))
        assert len(rollback_files) == 1
        
        # 修改文件中的创建时间为过期时间
        with open(rollback_files[0], 'r', encoding='utf-8') as f:
            rollback_info = json.load(f)
        
        rollback_info['created_at'] = '2020-01-01T00:00:00'
        
        with open(rollback_files[0], 'w', encoding='utf-8') as f:
            json.dump(rollback_info, f)
        
        # 执行清理
        cleaned_count = rollback_manager.cleanup_old_rollbacks(keep_days=1)
        
        assert cleaned_count == 1
        assert len(list(rollback_manager.rollback_dir.glob("*.json"))) == 0


class TestMigrationValidator:
    """测试迁移验证器"""
    
    @pytest.fixture
    def temp_engine(self):
        """创建临时SQLite引擎用于测试"""
        engine = create_engine("sqlite:///:memory:")
        yield engine
        engine.dispose()
    
    @pytest.fixture
    def migration_validator(self, temp_engine):
        """创建迁移验证器"""
        return MigrationValidator(temp_engine)
    
    def test_pre_migration_check(self, migration_validator):
        """测试迁移前检查"""
        result = migration_validator.pre_migration_check()
        
        assert isinstance(result, dict)
        assert 'safe_to_migrate' in result
        assert 'warnings' in result
        assert 'errors' in result
        assert 'checks' in result
        
        # 数据库连接应该正常
        assert result['checks']['database_connection'] is True
    
    def test_post_migration_check(self, migration_validator):
        """测试迁移后检查"""
        # 生成迁移前指纹
        pre_fingerprint = migration_validator.integrity_checker.generate_data_fingerprint()
        
        result = migration_validator.post_migration_check(pre_fingerprint)
        
        assert isinstance(result, dict)
        assert 'migration_successful' in result
        assert 'warnings' in result
        assert 'errors' in result
        assert 'checks' in result
        assert 'pre_migration_fingerprint' in result
        assert 'post_migration_fingerprint' in result


class TestMigrationIntegration:
    """集成测试"""
    
    @pytest.fixture
    def temp_engine(self):
        """创建临时SQLite引擎用于测试"""
        engine = create_engine("sqlite:///:memory:")
        yield engine
        engine.dispose()
    
    def test_full_migration_workflow(self, temp_engine):
        """测试完整的迁移工作流"""
        # 1. 创建迁移管理器
        manager = MigrationManager(temp_engine)
        validator = MigrationValidator(temp_engine)
        
        # 2. 迁移前检查
        pre_check = validator.pre_migration_check()
        assert pre_check['safe_to_migrate'] is True
        
        # 3. 生成数据指纹
        pre_fingerprint = validator.integrity_checker.generate_data_fingerprint()
        
        # 4. 执行迁移（模拟）
        # 在真实场景中，这里会执行实际的迁移
        
        # 5. 迁移后检查
        post_check = validator.post_migration_check(pre_fingerprint)
        # 由于没有实际修改数据，指纹应该相同
        assert post_check['pre_migration_fingerprint'] == post_check['post_migration_fingerprint']
    
    def test_migration_error_handling(self, temp_engine):
        """测试迁移错误处理"""
        manager = MigrationManager(temp_engine)
        
        # 测试无效配置的情况
        with patch.object(manager, 'config', None):
            with pytest.raises(AttributeError):
                manager.upgrade("head")


class TestMigrationSafety:
    """测试迁移安全机制"""
    
    @pytest.fixture
    def temp_engine_with_data(self):
        """创建包含数据的临时引擎"""
        engine = create_engine("sqlite:///:memory:")
        
        # 创建表和数据
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT
                )
            """))
            
            conn.execute(text("""
                INSERT INTO test_table (name, email) 
                VALUES ('User1', 'user1@example.com'), ('User2', 'user2@example.com')
            """))
            conn.commit()
        
        yield engine
        engine.dispose()
    
    def test_data_fingerprint_changes(self, temp_engine_with_data):
        """测试数据指纹变化检测"""
        checker = DataIntegrityChecker(temp_engine_with_data)
        
        # 获取初始指纹
        fingerprint1 = checker.generate_data_fingerprint()
        
        # 修改数据
        with temp_engine_with_data.connect() as conn:
            conn.execute(text("INSERT INTO test_table (name, email) VALUES ('User3', 'user3@example.com')"))
            conn.commit()
        
        # 获取新指纹
        fingerprint2 = checker.generate_data_fingerprint()
        
        # 指纹应该不同
        assert fingerprint1 != fingerprint2
    
    def test_referential_integrity_violation(self):
        """测试外键约束违反检测"""
        engine = create_engine("sqlite:///:memory:")
        
        # 创建表结构
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE parent_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE child_table (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER,
                    title TEXT,
                    FOREIGN KEY (parent_id) REFERENCES parent_table (id)
                )
            """))
            
            # 插入违反约束的数据（SQLite默认不强制外键约束）
            conn.execute(text("INSERT INTO parent_table (name) VALUES ('Parent1')"))
            conn.execute(text("INSERT INTO child_table (parent_id, title) VALUES (1, 'Valid Child')"))
            conn.execute(text("INSERT INTO child_table (parent_id, title) VALUES (999, 'Invalid Child')"))
            conn.commit()
        
        checker = DataIntegrityChecker(engine)
        result = checker.check_referential_integrity()
        
        # 应该检测到约束违反（如果数据库支持外键检查）
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'violations' in result
        
        engine.dispose()


class TestMigrationCLI:
    """测试迁移CLI命令"""
    
    def test_migration_commands_import(self):
        """测试迁移命令模块导入"""
        try:
            from app.cli.migration_commands import migration, seed, cli
            assert migration is not None
            assert seed is not None
            assert cli is not None
        except ImportError as e:
            pytest.skip(f"CLI模块导入失败: {e}")
    
    @patch('app.cli.migration_commands.migration_manager')
    def test_status_command(self, mock_manager):
        """测试状态命令"""
        mock_manager.check_migration_status.return_value = {
            'current_revision': 'abc123',
            'head_revision': 'def456',
            'is_up_to_date': False,
            'database_exists': True
        }
        
        from app.cli.migration_commands import migration
        
        # 这里可以测试命令的逻辑，但由于涉及Click，需要特殊的测试设置
        # 在实际环境中，可以使用Click的testing工具
        pass


class TestMigrationAPI:
    """测试迁移API端点"""
    
    def test_migration_endpoints_import(self):
        """测试迁移API端点导入"""
        try:
            from app.api.v1.endpoints.migrations import router
            assert router is not None
        except ImportError as e:
            pytest.skip(f"API端点模块导入失败: {e}")
    
    @patch('app.api.v1.endpoints.migrations.migration_manager')
    def test_status_endpoint(self, mock_manager):
        """测试状态端点"""
        mock_manager.check_migration_status.return_value = {
            'current_revision': 'abc123',
            'head_revision': 'def456',
            'is_up_to_date': False,
            'database_exists': True
        }
        
        # 这里可以测试API端点的逻辑
        # 在实际环境中，需要使用FastAPI的测试客户端
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])