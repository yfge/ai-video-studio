#!/usr/bin/env python3
"""
MySQL连接测试脚本

测试MySQL数据库连接和基本操作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_mysql_connection():
    """测试MySQL连接"""
    print("=" * 60)
    print("MySQL连接测试")
    print("=" * 60)

    try:
        # 测试PyMySQL直接连接
        print("1. 测试PyMySQL直接连接...")
        import pymysql

        connection = pymysql.connect(
            host="127.0.0.1",
            port=13306,
            user="root",
            password="Pa88word",
            database="ai_video_studio",
            charset="utf8mb4",
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"   ✅ MySQL版本: {version}")

            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()[0]
            print(f"   ✅ 当前数据库: {database}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   ✅ 表数量: {len(tables)}")
            if tables:
                print(f"   表列表: {[table[0] for table in tables]}")

        connection.close()
        print("   ✅ PyMySQL连接测试成功")

    except Exception as e:
        print(f"   ❌ PyMySQL连接失败: {str(e)}")
        return False

    try:
        # 测试SQLAlchemy连接
        print("\n2. 测试SQLAlchemy连接...")
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"   ✅ SQLAlchemy连接成功，MySQL版本: {version}")

            result = conn.execute(text("SELECT DATABASE()"))
            database = result.fetchone()[0]
            print(f"   ✅ 当前数据库: {database}")

    except Exception as e:
        print(f"   ❌ SQLAlchemy连接失败: {str(e)}")
        return False

    try:
        # 测试配置加载
        print("\n3. 测试配置加载...")
        from app.core.config import settings

        print(f"   ✅ 数据库URL: {settings.DATABASE_URL}")
        print(f"   ✅ 项目名称: {settings.PROJECT_NAME}")

    except Exception as e:
        print(f"   ❌ 配置加载失败: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有连接测试通过!")
    print("=" * 60)
    return True


def test_database_operations():
    """测试数据库基本操作"""
    print("\n" + "=" * 60)
    print("数据库操作测试")
    print("=" * 60)

    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # 创建测试表
            print("1. 创建测试表...")
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
                )
            )
            conn.commit()
            print("   ✅ 测试表创建成功")

            # 插入测试数据
            print("\n2. 插入测试数据...")
            conn.execute(
                text(
                    """
                INSERT INTO test_table (name) VALUES ('测试数据')
            """
                )
            )
            conn.commit()
            print("   ✅ 测试数据插入成功")

            # 查询测试数据
            print("\n3. 查询测试数据...")
            result = conn.execute(text("SELECT * FROM test_table"))
            rows = result.fetchall()
            print(f"   ✅ 查询到 {len(rows)} 条记录")
            for row in rows:
                print(f"      ID: {row[0]}, Name: {row[1]}, Created: {row[2]}")

            # 清理测试表
            print("\n4. 清理测试表...")
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.commit()
            print("   ✅ 测试表清理成功")

        print("\n" + "=" * 60)
        print("✅ 数据库操作测试通过!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"   ❌ 数据库操作测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_mysql_connection()
    if success:
        test_database_operations()
    else:
        sys.exit(1)
