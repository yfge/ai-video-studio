"""
简化测试 - 验证基本功能
"""

import os
import sys

import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.unit
def test_basic_functionality():
    """测试基本功能"""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert True is True


@pytest.mark.unit
def test_sqlite_memory_database():
    """测试SQLite内存数据库"""
    import sqlite3

    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 创建测试表
    cursor.execute(
        """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """
    )

    # 插入测试数据
    cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
    conn.commit()

    # 查询数据
    cursor.execute("SELECT name FROM test_table WHERE id = 1")
    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "test"

    conn.close()


@pytest.mark.unit
def test_json_serialization():
    """测试JSON序列化"""
    import json

    test_data = {
        "name": "Test IP",
        "tags": ["tag1", "tag2"],
        "metadata": {"key": "value"},
    }

    # 序列化
    json_str = json.dumps(test_data)

    # 反序列化
    parsed_data = json.loads(json_str)

    assert parsed_data["name"] == "Test IP"
    assert parsed_data["tags"] == ["tag1", "tag2"]
    assert parsed_data["metadata"]["key"] == "value"


@pytest.mark.unit
def test_alembic_import():
    """测试Alembic导入"""
    try:
        from alembic import command
        from alembic.config import Config

        assert command is not None
        assert Config is not None
    except ImportError:
        pytest.fail("Alembic not properly installed")


@pytest.mark.unit
def test_sqlalchemy_import():
    """测试SQLAlchemy导入"""
    try:
        from sqlalchemy import Column, create_engine
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker

        assert create_engine is not None
        assert Column is not None
        assert declarative_base is not None
        assert sessionmaker is not None
    except ImportError:
        pytest.fail("SQLAlchemy not properly installed")


@pytest.mark.unit
def test_factory_boy_import():
    """测试Factory Boy导入"""
    try:
        import factory

        assert factory is not None
    except ImportError:
        pytest.fail("Factory Boy not properly installed")


@pytest.mark.unit
def test_pytest_import():
    """测试pytest导入"""
    try:
        import pytest

        assert pytest is not None
    except ImportError:
        pytest.fail("pytest not properly installed")
