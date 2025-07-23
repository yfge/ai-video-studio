from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "AI图片生成API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./ai_pic.db"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif"]
    
    # AI服务配置
    AI_SERVICE_URL: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    
    # Stability AI配置
    STABILITY_API_KEY: Optional[str] = None
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 