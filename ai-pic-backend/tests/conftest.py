"""
pytest 配置文件

定义测试fixtures和全局配置
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Generator, Iterable, List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.middleware import (
    get_current_active_user,
    get_current_admin_user,
    get_current_superuser,
)
from tests.unit.test_database import get_test_db as unit_get_test_db


def get_test_db() -> Generator:
    """兼容旧测试导入路径，复用单元测试数据库会话生成器。"""
    yield from unit_get_test_db()


def override_get_db() -> Generator:
    """用于 FastAPI 依赖覆盖的数据库会话生成器。"""
    yield from get_test_db()


@pytest.fixture
def test_db_session(db_session):
    """兼容旧测试所需的数据库会话 fixture。"""
    yield db_session


@pytest.fixture
def mock_ai_service(monkeypatch):
    """mock AI 服务，避免真实外部依赖。"""
    from app.services import ai_service as ai_module

    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    created_files: List[Path] = []

    class _MockAIService:
        async def generate_virtual_ip_image(
            self,
            ip_name: str,
            description: str,
            style: str,
            category: str,
            model: str,
            additional_prompts: Iterable[str] | None = None,
            **_: str,
        ) -> dict:
            filename = f"mock-ai-{uuid4().hex}.png"
            file_path = uploads_dir / filename
            file_path.write_bytes(b"mock image bytes")
            created_files.append(file_path)
            return {
                "prompt": f"mock prompt for {ip_name}",
                "style": style,
                "model_used": model or "mock-model",
                "generation_method": "mock-provider",
                "local_file_path": str(file_path),
                "oss_upload": None,
                "usage": {"provider": "mock-provider", "model": model or "mock-model"},
                "additional_prompts": list(additional_prompts or []),
            }

        async def generate_story_outline(self, **_: str) -> dict:
            normalized = {
                "premise": "Mock premise",
                "synopsis": "Mock synopsis",
                "main_conflict": "Mock conflict",
                "resolution": "Mock resolution",
                "main_characters": [
                    {"name": "Hero", "role": "protagonist"},
                    {"name": "Guide", "role": "mentor"},
                ],
                "character_relationships": {"Hero": {"Guide": "mentor"}},
            }
            return {
                "normalized": normalized,
                "prompt": "mock-story-prompt",
                "generation_method": "mock-provider:story",
            }

        async def generate_episodes(self, episode_count: int = 1, **_: str) -> dict:
            episodes_payload = {
                "episodes": [
                    {
                        "episode_number": idx + 1,
                        "title": f"Mock Episode {idx + 1}",
                        "summary": "Mock summary",
                        "plot_points": [{"order": 1, "description": "Mock plot"}],
                        "character_arcs": {"Hero": "Learns trust"},
                        "conflicts": ["Mock conflict"],
                        "scene_count": 3,
                    }
                    for idx in range(episode_count or 1)
                ]
            }
            return {
                "content": json.dumps(episodes_payload, ensure_ascii=False),
                "prompt": "mock-episode-prompt",
                "generation_method": "mock-provider:episodes",
            }

        async def generate_script(self, **_: str) -> dict:
            script_payload = {
                "content": "INT. ROOM - DAY\nMock dialogue.",
                "scenes": [
                    {
                        "scene_number": 1,
                        "location": "Room",
                        "time": "Day",
                        "description": "Mock scene description",
                    }
                ],
                "dialogues": [
                    {"scene_number": 1, "character": "Hero", "content": "Hello there!"}
                ],
                "stage_directions": [
                    {"scene_number": 1, "direction": "Camera pans across the room."}
                ],
            }
            return {
                "content": script_payload,
                "prompt": "mock-script-prompt",
                "generation_method": "mock-provider:scripts",
            }

    original_service = ai_module.ai_service
    mock_service = _MockAIService()
    monkeypatch.setattr(ai_module, "ai_service", mock_service)

    try:
        yield mock_service
    finally:
        monkeypatch.setattr(ai_module, "ai_service", original_service)
        for file_path in created_files:
            if file_path.exists():
                file_path.unlink()


@pytest.fixture
def driver():
    """提供 Selenium WebDriver，如缺少依赖则跳过相关测试。"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except Exception:
        pytest.skip("Selenium 未安装，跳过依赖 WebDriver 的测试")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        driver_instance = webdriver.Chrome(options=options)
    except Exception:
        pytest.skip("Chrome WebDriver 不可用，跳过相关测试")
        return

    try:
        yield driver_instance
    finally:
        driver_instance.quit()


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
def db(db_session):
    """兼容旧用例的 db 别名"""
    yield db_session


@pytest.fixture
def client(db_session):
    """测试客户端fixture"""
    # 确保存在默认活跃管理员用户，便于通过权限校验
    from app.models.user import User

    admin_user = (
        db_session.query(User).filter(User.username == "test_admin").first()
    )
    if not admin_user:
        admin_user = User(
            username="test_admin",
            email="test_admin@example.com",
            hashed_password="not-used-in-tests",
            full_name="Test Admin",
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=True,
            is_superuser=True,
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_active_user():
        return admin_user

    def override_admin_user():
        return admin_user

    def override_superuser():
        return admin_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_active_user
    app.dependency_overrides[get_current_admin_user] = override_admin_user
    app.dependency_overrides[get_current_superuser] = override_superuser

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
