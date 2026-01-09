"""
pytest 配置文件

集中注册 fixtures 插件，并保留旧测试引用的兼容函数。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Generator

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.unit.test_database import get_test_db as unit_get_test_db

pytest_plugins = [
    "tests.fixtures.asyncio_loop",
    "tests.fixtures.db",
    "tests.fixtures.client",
    "tests.fixtures.mock_ai_service",
    "tests.fixtures.selenium_driver",
    "tests.fixtures.markers",
]


def get_test_db() -> Generator:
    """兼容旧测试导入路径，复用单元测试数据库会话生成器。"""
    yield from unit_get_test_db()


def override_get_db() -> Generator:
    """用于 FastAPI 依赖覆盖的数据库会话生成器。"""
    yield from get_test_db()
