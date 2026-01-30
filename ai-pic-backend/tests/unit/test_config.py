"""
测试环境配置
"""

import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    """测试环境配置"""

    # 项目配置
    PROJECT_NAME: str = "AI图片生成API - 测试环境"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = "test-secret-key-not-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 测试数据库配置
    TEST_DATABASE_URL: str = "sqlite:///./test.db"

    # 内存数据库（更快的测试）
    MEMORY_DATABASE_URL: str = "sqlite:///:memory:"

    # Redis配置（测试用）
    REDIS_URL: str = "redis://localhost:6379/1"  # 使用不同的数据库

    # CORS配置
    ALLOWED_HOSTS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 文件上传配置
    UPLOAD_DIR: str = tempfile.gettempdir()
    MAX_FILE_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".gif"]

    # AI服务配置（测试用mock）
    AI_SERVICE_URL: str = "http://localhost:8000/mock"
    AI_API_KEY: str = "test-api-key"

    # OpenAI配置（测试用）
    OPENAI_API_KEY: str = "test-openai-key"

    # Stability AI配置（测试用）
    STABILITY_API_KEY: str = "test-stability-key"

    # 测试特定配置
    TESTING: bool = True
    DEBUG: bool = True

    # 邮件配置（测试用）
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = "test@example.com"
    SMTP_PASSWORD: str = "test-password"

    class Config:
        env_file = ".env.test"
        case_sensitive = True


# 创建测试设置实例
test_settings = TestSettings()


def get_test_database_url(use_memory: bool = False) -> str:
    """获取测试数据库URL"""
    if use_memory:
        return test_settings.MEMORY_DATABASE_URL
    return test_settings.TEST_DATABASE_URL


def get_test_upload_dir() -> Path:
    """获取测试上传目录"""
    test_dir = Path(tempfile.gettempdir()) / "ai_pic_test_uploads"
    test_dir.mkdir(exist_ok=True)
    return test_dir


def cleanup_test_files():
    """清理测试文件"""
    import shutil

    test_dir = get_test_upload_dir()
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # 清理测试数据库文件
    test_db_path = Path("test.db")
    if test_db_path.exists():
        test_db_path.unlink()
