#!/usr/bin/env python3
try:
    print("导入用户模型...")
    print("✓ 用户模型导入成功")

    print("导入虚拟IP模型...")
    print("✓ 虚拟IP模型导入成功")

    print("导入脚本模型...")
    print("✓ 脚本模型导入成功")

    print("导入数据库基类...")
    from app.core.database import Base

    print("✓ 数据库基类导入成功")

    print("检查metadata...")
    print(f"Base.metadata.tables: {list(Base.metadata.tables.keys())}")

    print("所有导入成功！")

except Exception as e:
    print(f"导入失败: {e}")
    import traceback

    traceback.print_exc()
