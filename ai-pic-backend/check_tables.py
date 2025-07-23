#!/usr/bin/env python3
from sqlalchemy import create_engine, inspect, text

# 检查现有数据库
engine = create_engine('sqlite:///./ai_pic.db')
inspector = inspect(engine)
tables = inspector.get_table_names()

print("现有数据库中的表:")
for table in tables:
    print(f"  - {table}")

if not tables:
    print("  没有找到任何表")

# 检查alembic版本
with engine.connect() as conn:
    try:
        result = conn.execute(text('SELECT version_num FROM alembic_version'))
        version = result.scalar()
        print(f"当前版本: {version}")
    except Exception as e:
        print(f"检查版本时出错: {e}")

engine.dispose()

# 检查临时数据库
import tempfile
import os

db_fd, db_path = tempfile.mkstemp(suffix='.db')
os.close(db_fd)

try:
    from alembic import command
    from alembic.config import Config
    
    db_url = f"sqlite:///{db_path}"
    print(f"\n测试数据库: {db_url}")
    
    # 配置Alembic
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    # 检查迁移前的状态
    print("迁移前检查...")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables_before = inspector.get_table_names()
    print(f"迁移前的表: {tables_before}")
    engine.dispose()
    
    # 运行迁移
    print("运行迁移...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("迁移完成")
    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 检查迁移后的状态
    print("迁移后检查...")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    
    print("迁移后的表:")
    for table in tables_after:
        print(f"  - {table}")
    
    if not tables_after:
        print("  没有找到任何表")
    
    # 检查alembic版本表
    with engine.connect() as conn:
        try:
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            version = result.scalar()
            print(f"新数据库版本: {version}")
        except Exception as e:
            print(f"检查新数据库版本时出错: {e}")
    
    engine.dispose()
    
finally:
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except:
            pass 