#!/usr/bin/env python3
import os
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

# 创建临时数据库
db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)

try:
    db_url = f"sqlite:///{db_path}"
    print(f"测试数据库: {db_url}")

    # 配置Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    print("运行迁移...")

    # 手动运行迁移脚本

    # 创建引擎
    engine = create_engine(db_url)

    # 手动创建表
    print("手动创建表...")
    from app.core.database import Base

    Base.metadata.create_all(engine)

    # 检查表
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("手动创建后的表:")
    for table in tables:
        print(f"  - {table}")

    engine.dispose()

    # 现在尝试用alembic升级
    print("\n现在尝试alembic升级...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("Alembic升级成功")
    except Exception as e:
        print(f"Alembic升级失败: {e}")
        import traceback

        traceback.print_exc()

    # 再次检查表
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Alembic升级后的表:")
    for table in tables:
        print(f"  - {table}")

    engine.dispose()

finally:
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except:
            pass
