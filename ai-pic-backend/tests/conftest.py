"""
pytest 配置文件

定义测试fixtures和全局配置
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.core.database import Base, get_db
from app.core.config import settings
from tests.unit.test_database import get_test_db as unit_get_test_db


def get_test_db() -> Generator:
    """兼容旧测试导入路径，复用单元测试数据库会话生成器。"""
    yield from unit_get_test_db()


def override_get_db() -> Generator:
    """用于 FastAPI 依赖覆盖的数据库会话生成器。"""
    yield from get_test_db()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """测试数据库fixture"""
    # 使用SQLite内存数据库进行测试
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # 清理
    os.unlink("test.db")


@pytest.fixture
def db_session(test_db):
    """数据库会话fixture"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """测试客户端fixture"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """认证头fixture"""
    # 创建测试用户并登录
    login_data = {
        "username": "admin",
        "password": "Ai7dio"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        # 如果登录失败，返回空头，测试会相应失败
        return {}


@pytest.fixture
def test_virtual_ip_data():
    """测试虚拟IP数据"""
    return {
        "name": "测试IP",
        "description": "用于测试的虚拟IP",
        "tags": ["test", "ai"],
        "background_story": "这是一个测试用的虚拟IP角色",
        "style_prompt": "realistic, professional",
        "is_active": True,
        "is_public": False
    }


@pytest.fixture
def skip_if_no_openai():
    """如果没有OpenAI API密钥则跳过测试"""
    if not getattr(settings, 'OPENAI_API_KEY', None):
        pytest.skip("需要OPENAI_API_KEY环境变量")


@pytest.fixture 
def skip_if_no_oss():
    """如果没有OSS配置则跳过测试"""
    required_oss_configs = [
        'ALIYUN_ACCESS_KEY_ID',
        'ALIYUN_ACCESS_KEY_SECRET', 
        'ALIYUN_OSS_ENDPOINT',
        'ALIYUN_OSS_BUCKET'
    ]
    
    missing_configs = [
        config for config in required_oss_configs 
        if not getattr(settings, config, None)
    ]
    
    if missing_configs:
        pytest.skip(f"需要OSS配置: {', '.join(missing_configs)}")


# 测试标记的自动应用
def pytest_collection_modifyitems(config, items):
    """根据测试名称自动添加标记"""
    for item in items:
        # 根据文件路径添加标记
        if "test_diagnostic" in item.nodeid:
            item.add_marker(pytest.mark.diagnostic)
        if "test_openai" in item.nodeid or "openai" in item.nodeid:
            item.add_marker(pytest.mark.openai)
            item.add_marker(pytest.mark.external)
        if "test_oss" in item.nodeid or "oss" in item.nodeid:
            item.add_marker(pytest.mark.oss)
            item.add_marker(pytest.mark.external)
        if "test_database" in item.nodeid or "database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "e2e" in item.nodeid or "end_to_end" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


# 控制台输出美化
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """自定义测试结果总结"""
    if exitstatus == 0:
        terminalreporter.write_line(
            "\n🎉 所有测试通过！AI图像生成系统运行正常。",
            green=True
        )
    else:
        terminalreporter.write_line(
            "\n❌ 部分测试失败，请检查上述错误信息。",
            red=True
        )
