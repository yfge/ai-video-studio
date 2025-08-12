#!/usr/bin/env python3
"""
MySQL数据库初始化脚本

用于创建数据库和设置基础配置
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pymysql
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_mysql_url(database_url: str):
    """解析MySQL数据库URL"""
    import re
    
    pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
    match = re.match(pattern, database_url)
    
    if not match:
        raise ValueError(f"无法解析数据库URL: {database_url}")
    
    return {
        'user': match.group(1),
        'password': match.group(2),
        'host': match.group(3),
        'port': int(match.group(4)),
        'database': match.group(5)
    }


def create_database():
    """创建数据库"""
    try:
        # 解析数据库连接信息
        db_config = parse_mysql_url(settings.DATABASE_URL)
        database_name = db_config.pop('database')
        
        logger.info(f"连接到MySQL服务器: {db_config['host']}:{db_config['port']}")
        
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(**db_config)
        
        try:
            with connection.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                if cursor.fetchone():
                    logger.info(f"数据库 '{database_name}' 已存在")
                else:
                    # 创建数据库
                    cursor.execute(f"""
                        CREATE DATABASE `{database_name}` 
                        CHARACTER SET utf8mb4 
                        COLLATE utf8mb4_unicode_ci
                    """)
                    logger.info(f"数据库 '{database_name}' 创建成功")
                
                # 显示数据库信息
                cursor.execute(f"SHOW CREATE DATABASE `{database_name}`")
                result = cursor.fetchone()
                logger.info(f"数据库配置: {result[1]}")
                
                connection.commit()
                
        finally:
            connection.close()
            
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False


def test_connection():
    """测试数据库连接"""
    try:
        from app.core.database import engine
        
        logger.info("测试数据库连接...")
        
        # 测试连接
        connection = engine.connect()
        connection.close()
        
        logger.info("数据库连接测试成功")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("MySQL数据库初始化脚本")
    print("=" * 60)
    
    print(f"项目目录: {project_root}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print()
    
    # 创建数据库
    if not create_database():
        sys.exit(1)
    
    print()
    
    # 测试连接
    if not test_connection():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ 数据库初始化成功!")
    print()
    print("下一步操作:")
    print("1. 运行数据库迁移: alembic upgrade head")
    print("2. 或使用脚本: python migrate.py")
    print("=" * 60)


if __name__ == "__main__":
    main()