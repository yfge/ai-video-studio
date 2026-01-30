"""
基础测试 - 验证测试框架是否正常工作
"""

import pytest
from tests.unit.test_database import reset_test_database, test_db


@pytest.mark.unit
def test_basic_functionality():
    """测试基本功能"""
    assert 1 + 1 == 2
    assert "hello" == "hello"
    assert True is True


@pytest.mark.unit
def test_database_connection():
    """测试数据库连接"""
    # 重置测试数据库
    reset_test_database()

    # 获取会话
    session = next(test_db.get_session())

    try:
        # 执行简单查询
        result = session.execute("SELECT 1 as test_value")
        value = result.scalar()
        assert value == 1

    finally:
        session.close()


@pytest.mark.unit
def test_imports():
    """测试重要模块导入"""
    # 测试模型导入
    # 测试配置导入
    from app.core.test_config import test_settings
    from app.core.test_database import test_db
    from app.models.user import User
    from app.models.virtual_ip import VirtualIP

    # 基本断言
    assert User is not None
    assert VirtualIP is not None
    assert test_settings is not None
    assert test_db is not None
