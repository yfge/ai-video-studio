"""
工作的迁移测试
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.mark.integration
def test_database_creation_with_sqlalchemy():
    """测试使用SQLAlchemy直接创建数据库"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        db_url = f"sqlite:///{db_path}"

        # 创建引擎
        engine = create_engine(db_url)

        # 导入模型并创建表
        from app.core.database import Base

        # 创建所有表
        Base.metadata.create_all(engine)

        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 验证关键表存在
        expected_tables = ["users", "virtual_ips", "stories", "episodes", "scripts"]
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in {tables}"

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


@pytest.mark.integration
def test_sqlite_crud_operations():
    """测试SQLite CRUD操作"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        db_url = f"sqlite:///{db_path}"

        # 创建引擎
        engine = create_engine(db_url)

        # 导入模型并创建表
        from app.core.database import Base

        # 创建所有表
        Base.metadata.create_all(engine)

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

            # 测试插入虚拟IP
            conn.execute(
                text(
                    """
                INSERT INTO virtual_ips (name, description, tags, is_active, is_public)
                VALUES ('Test IP', 'Test description', '["tag1", "tag2"]', 1, 0)
            """
                )
            )
            conn.commit()

            # 测试查询虚拟IP
            result = conn.execute(
                text("SELECT name, tags FROM virtual_ips WHERE name = 'Test IP'")
            )
            vip = result.fetchone()
            assert vip is not None
            assert vip[0] == "Test IP"

            # 测试插入故事
            conn.execute(
                text(
                    """
                INSERT INTO stories (title, genre, premise, synopsis, main_characters, character_relationships, generation_params)
                VALUES ('Test Story', 'Romance', 'Test premise', 'Test synopsis', '[]', '{}', '{}')
            """
                )
            )
            conn.commit()

            # 测试查询故事
            result = conn.execute(
                text("SELECT title FROM stories WHERE title = 'Test Story'")
            )
            story = result.fetchone()
            assert story is not None
            assert story[0] == "Test Story"

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


@pytest.mark.integration
def test_foreign_key_relationships():
    """测试外键关系"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        db_url = f"sqlite:///{db_path}"

        # 创建引擎
        engine = create_engine(db_url)

        # 导入模型并创建表
        from app.core.database import Base

        # 创建所有表
        Base.metadata.create_all(engine)

        # 测试外键关系
        with engine.connect() as conn:
            # 插入虚拟IP
            conn.execute(
                text(
                    """
                INSERT INTO virtual_ips (name, description, is_active, is_public)
                VALUES ('Test IP', 'Test description', 1, 0)
            """
                )
            )
            conn.commit()

            # 获取虚拟IP的ID
            result = conn.execute(
                text("SELECT id FROM virtual_ips WHERE name = 'Test IP'")
            )
            vip_id = result.scalar()
            assert vip_id is not None

            # 插入虚拟IP图像
            conn.execute(
                text(
                    """
                INSERT INTO virtual_ip_images (virtual_ip_id, filename, original_filename, file_path, file_size, mime_type, category)
                VALUES (:vip_id, 'test.jpg', 'test.jpg', '/uploads/test.jpg', 1024, 'image/jpeg', 'avatar')
            """
                ),
                {"vip_id": vip_id},
            )
            conn.commit()

            # 测试关系查询
            result = conn.execute(
                text(
                    """
                SELECT vi.name, vii.filename
                FROM virtual_ips vi
                JOIN virtual_ip_images vii ON vi.id = vii.virtual_ip_id
                WHERE vi.name = 'Test IP'
            """
                )
            )
            relation = result.fetchone()
            assert relation is not None
            assert relation[0] == "Test IP"
            assert relation[1] == "test.jpg"

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


@pytest.mark.integration
def test_json_columns():
    """测试JSON列的SQLite兼容性"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    try:
        db_url = f"sqlite:///{db_path}"

        # 创建引擎
        engine = create_engine(db_url)

        # 导入模型并创建表
        from app.core.database import Base

        # 创建所有表
        Base.metadata.create_all(engine)

        # 测试JSON列
        with engine.connect() as conn:
            # 测试虚拟IP的JSON标签
            conn.execute(
                text(
                    """
                INSERT INTO virtual_ips (name, description, tags, style_reference_images, is_active, is_public)
                VALUES ('Test IP', 'Test description', '["tag1", "tag2", "tag3"]', '["http://example.com/image.jpg"]', 1, 0)
            """
                )
            )
            conn.commit()

            # 查询JSON数据
            result = conn.execute(
                text(
                    "SELECT tags, style_reference_images FROM virtual_ips WHERE name = 'Test IP'"
                )
            )
            data = result.fetchone()
            assert data is not None
            assert data[0] == '["tag1", "tag2", "tag3"]'
            assert data[1] == '["http://example.com/image.jpg"]'

            # 测试故事的JSON字段
            conn.execute(
                text(
                    """
                INSERT INTO stories (title, genre, premise, synopsis, main_characters, character_relationships, generation_params)
                VALUES ('Test Story', 'Romance', 'Test premise', 'Test synopsis',
                        '[{"name": "Character1", "role": "protagonist"}]',
                        '{"Character1": {"Character2": "friend"}}',
                        '{"temperature": 0.7}')
            """
                )
            )
            conn.commit()

            # 查询故事JSON数据
            result = conn.execute(
                text(
                    "SELECT main_characters, character_relationships, generation_params FROM stories WHERE title = 'Test Story'"
                )
            )
            story_data = result.fetchone()
            assert story_data is not None
            assert '"name": "Character1"' in story_data[0]
            assert '"Character2": "friend"' in story_data[1]
            assert '"temperature": 0.7' in story_data[2]

        engine.dispose()

    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass
