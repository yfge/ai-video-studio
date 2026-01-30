"""
测试数据库配置和工具
"""

from typing import AsyncGenerator, Generator

from alembic import command
from alembic.config import Config
from app.core.database import Base
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from tests.unit.test_config import test_settings


class TestDatabase:
    """测试数据库管理器"""

    def __init__(self, use_memory: bool = True):
        self.use_memory = use_memory
        self.database_url = (
            test_settings.MEMORY_DATABASE_URL
            if use_memory
            else test_settings.TEST_DATABASE_URL
        )

        # 创建引擎
        self.engine = create_engine(
            self.database_url,
            connect_args=(
                {"check_same_thread": False, "isolation_level": "DEFERRED"}
                if "sqlite" in self.database_url
                else {}
            ),
            poolclass=StaticPool if use_memory else None,
            echo=False,  # 设置为True可以看到SQL语句
        )

        # 确保所有模型被加载以注册到 Base.metadata
        from app import models  # noqa: F401

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # 启用外键约束（SQLite）
        if "sqlite" in self.database_url:

            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def run_migrations(self):
        """运行迁移"""
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        # 运行迁移
        command.upgrade(alembic_cfg, "head")

    def reset_database(self):
        """重置数据库"""
        self.drop_tables()
        self.create_tables()


# 全局测试数据库实例
test_db = TestDatabase(use_memory=True)


def get_test_db() -> Generator[Session, None, None]:
    """获取测试数据库会话的依赖注入函数"""
    yield from test_db.get_session()


def setup_test_database():
    """设置测试数据库"""
    test_db.create_tables()


def teardown_test_database():
    """清理测试数据库"""
    test_db.drop_tables()


def reset_test_database():
    """重置测试数据库"""
    test_db.reset_database()


# 异步数据库支持（如果需要）
class AsyncTestDatabase:
    """异步测试数据库管理器"""

    def __init__(self, use_memory: bool = True):
        self.use_memory = use_memory
        self.database_url = (
            test_settings.MEMORY_DATABASE_URL
            if use_memory
            else test_settings.TEST_DATABASE_URL
        )

        # 转换为异步URL
        if self.database_url.startswith("sqlite:///"):
            self.async_database_url = self.database_url.replace(
                "sqlite:///", "sqlite+aiosqlite:///"
            )
        else:
            self.async_database_url = self.database_url

        # 创建异步引擎
        self.async_engine = create_async_engine(
            self.async_database_url,
            echo=False,
            poolclass=StaticPool if use_memory else None,
        )

        # 创建异步会话工厂
        self.AsyncSessionLocal = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        """创建所有表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """删除所有表"""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取异步数据库会话"""
        async with self.AsyncSessionLocal() as session:
            yield session

    async def reset_database(self):
        """重置数据库"""
        await self.drop_tables()
        await self.create_tables()


# 全局异步测试数据库实例
async_test_db = AsyncTestDatabase(use_memory=True)
