"""
简化的pytest配置文件
"""
import pytest
import tempfile
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


@pytest.fixture(scope="function")
def test_db_session() -> Generator[Session, None, None]:
    """为每个测试函数提供数据库会话"""
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    try:
        # 创建引擎
        engine = create_engine(f"sqlite:///{db_path}")
        
        # 导入模型并创建表
        from app.core.database import Base
        from app.models.user import User
        from app.models.virtual_ip import VirtualIP, VirtualIPImage
        from app.models.script import Story, Episode, Script, StoryCharacter, ScriptTemplate
        
        # 创建所有表
        Base.metadata.create_all(engine)
        
        # 创建会话
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        try:
            yield session
        finally:
            session.close()
            engine.dispose()
            
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


@pytest.fixture
def sample_image_data():
    """提供示例图片数据"""
    return {
        'filename': 'test_image.png',
        'content': b'fake_image_content',
        'content_type': 'image/png'
    }


@pytest.fixture
def mock_ai_service(mocker):
    """模拟AI服务"""
    mock_service = mocker.patch('app.services.ai_service.AIService')
    
    # 模拟图片生成
    mock_service.return_value.generate_image.return_value = {
        'success': True,
        'image_url': 'http://example.com/generated_image.png',
        'prompt': 'test prompt',
        'model': 'test-model'
    }
    
    return mock_service


# 测试标记
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e 