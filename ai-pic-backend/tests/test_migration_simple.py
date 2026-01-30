"""
简化迁移测试
"""

import os
import tempfile

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def _resolve_upgrade_target(db_url: str) -> str:
    """Resolve the Alembic upgrade target for the given database URL.

    The project primarily targets MySQL in production. Some later migrations use
    MySQL-only DDL (e.g. type/constraint alterations) that SQLite can't execute.
    For the SQLite-based unit suite, we validate a compatible prefix of the
    migration history.
    """

    if db_url.startswith("sqlite:"):
        return "0002_add_user_management_fields"
    return "head"


@pytest.mark.integration
def test_migration_basic():
    """测试基本迁移功能"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # 关闭文件描述符

    try:
        db_url = f"sqlite:///{db_path}"

        # 配置Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # 运行迁移
        command.upgrade(alembic_cfg, _resolve_upgrade_target(db_url))

        # 检查表是否存在
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        # 验证关键表存在
        expected_tables = ["users", "virtual_ips", "stories", "alembic_version"]
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in {tables}"

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass  # 忽略权限错误


@pytest.mark.integration
def test_migration_sqlite_compatibility():
    """测试SQLite兼容性"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # 关闭文件描述符

    try:
        db_url = f"sqlite:///{db_path}"

        # 配置Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # 运行迁移
        command.upgrade(alembic_cfg, _resolve_upgrade_target(db_url))

        # 创建引擎和连接
        engine = create_engine(db_url)

        # 测试基本SQL操作
        with engine.connect() as conn:
            # 测试插入用户
            conn.execute(
                text(
                    """
                INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
                VALUES ('testuser', 'test@example.com', 'hashed_password', 'Test User', 1, 0)
            """
                )
            )
            conn.commit()

            # 测试查询用户
            result = conn.execute(
                text("SELECT username FROM users WHERE username = 'testuser'")
            )
            user = result.fetchone()
            assert user is not None
            assert user[0] == "testuser"

            # 测试JSON列（如果支持）
            conn.execute(
                text(
                    """
                INSERT INTO virtual_ips (name, description, tags, is_active, is_public)
                VALUES ('Test IP', 'Test description', '["tag1", "tag2"]', 1, 0)
            """
                )
            )
            conn.commit()

            result = conn.execute(
                text("SELECT tags FROM virtual_ips WHERE name = 'Test IP'")
            )
            tags = result.fetchone()
            assert tags is not None

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass  # 忽略权限错误


@pytest.mark.integration
def test_migration_downgrade():
    """测试迁移回退"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # 关闭文件描述符

    try:
        db_url = f"sqlite:///{db_path}"

        # 配置Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        # 运行迁移
        command.upgrade(alembic_cfg, _resolve_upgrade_target(db_url))

        # 检查表存在
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        assert "users" in tables_before
        engine.dispose()

        # 回退迁移
        command.downgrade(alembic_cfg, "base")

        # 检查表被删除
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()

        # 只应该剩下alembic_version表
        assert "users" not in tables_after
        assert "virtual_ips" not in tables_after

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass  # 忽略权限错误
