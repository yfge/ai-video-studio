import logging

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


# 根据数据库类型设置连接参数
def get_engine_config():
    """根据数据库URL类型获取相应的引擎配置"""
    if "sqlite" in settings.DATABASE_URL:
        return {"connect_args": {"check_same_thread": False}}
    elif "mysql" in settings.DATABASE_URL:
        return {
            "pool_size": 20,
            "max_overflow": 0,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "connect_args": {"charset": "utf8mb4", "autocommit": False},
        }
    else:
        return {}


# 创建数据库引擎
engine_config = get_engine_config()
engine = create_engine(settings.DATABASE_URL, **engine_config)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


# 依赖注入函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
