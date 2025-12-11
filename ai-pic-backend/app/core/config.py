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
    DATABASE_URL: str = "mysql+pymysql://root:Pa88word@127.0.0.1:13306/ai_video_studio?charset=utf8mb4"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS配置  
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "localhost:8000", "127.0.0.1:8000", "*"]
    
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
    
    # 其他AI服务配置
    # 可灵AI（快手）- 双密钥认证
    KELING_API_KEY: Optional[str] = None
    KELING_SECRET_KEY: Optional[str] = None
    
    # 即梦AI - 双密钥认证  
    JIMENG_API_KEY: Optional[str] = None
    JIMENG_SECRET_KEY: Optional[str] = None
    
    # MiniMax配置
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_GROUP_ID: Optional[str] = None
    
    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # 火山引擎配置
    VOLCENGINE_API_KEY: Optional[str] = None
    VOLCENGINE_SECRET_KEY: Optional[str] = None
    VOLCENGINE_REGION: Optional[str] = None

    # Google Gemini / Vertex AI 配置（文本模型）
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_DEFAULT_MODEL: Optional[str] = "gemini-3-pro-preview"
    
    # 阿里云OSS配置
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_OSS_ENDPOINT: Optional[str] = None
    ALIYUN_OSS_BUCKET: Optional[str] = None
    ALIYUN_OSS_DOMAIN: Optional[str] = None
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    ENABLE_FILE_LOGGING: bool = True
    ENABLE_CONSOLE_LOGGING: bool = True
    LOG_BACKUP_COUNT: int = 7
    FEISHU_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


def _normalize_optional_str(value: Optional[str]) -> Optional[str]:
    """Trim whitespace and treat empty strings as None for optional secrets."""
    if value is None:
        return None
    value = value.strip()
    return value or None


# 规范化部分可选密钥，避免 ".env" 中留下空字符串时被误判为已配置
settings.GOOGLE_API_KEY = _normalize_optional_str(settings.GOOGLE_API_KEY)
settings.OPENAI_API_KEY = _normalize_optional_str(settings.OPENAI_API_KEY)
settings.STABILITY_API_KEY = _normalize_optional_str(settings.STABILITY_API_KEY)
settings.KELING_API_KEY = _normalize_optional_str(settings.KELING_API_KEY)
settings.KELING_SECRET_KEY = _normalize_optional_str(settings.KELING_SECRET_KEY)
settings.JIMENG_API_KEY = _normalize_optional_str(settings.JIMENG_API_KEY)
settings.JIMENG_SECRET_KEY = _normalize_optional_str(settings.JIMENG_SECRET_KEY)
settings.MINIMAX_API_KEY = _normalize_optional_str(settings.MINIMAX_API_KEY)
settings.MINIMAX_GROUP_ID = _normalize_optional_str(settings.MINIMAX_GROUP_ID)
settings.DEEPSEEK_API_KEY = _normalize_optional_str(settings.DEEPSEEK_API_KEY)
settings.VOLCENGINE_API_KEY = _normalize_optional_str(settings.VOLCENGINE_API_KEY)
settings.VOLCENGINE_SECRET_KEY = _normalize_optional_str(settings.VOLCENGINE_SECRET_KEY)
settings.VOLCENGINE_REGION = _normalize_optional_str(settings.VOLCENGINE_REGION)

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 
