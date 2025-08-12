#!/usr/bin/env python3
"""
数据库迁移脚本：从SQLite迁移到MySQL

此脚本用于将现有的SQLite数据迁移到MySQL数据库
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import pymysql
from sqlalchemy import create_engine, text
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_mysql_url(database_url: str) -> Dict[str, Any]:
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


def find_sqlite_db() -> str:
    """查找SQLite数据库文件"""
    possible_paths = [
        project_root / "ai_pic.db",
        project_root / "app.db",
        project_root / "database.db"
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    raise FileNotFoundError("找不到SQLite数据库文件")


def get_sqlite_tables(db_path: str) -> list:
    """获取SQLite数据库中的表列表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables


def migrate_table_data(sqlite_path: str, table_name: str, mysql_engine):
    """迁移单个表的数据"""
    logger.info(f"开始迁移表: {table_name}")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    try:
        # 获取SQLite表数据
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logger.info(f"表 {table_name} 无数据，跳过")
            return
        
        # 获取列名
        column_names = [description[0] for description in sqlite_cursor.description]
        
        # 构建MySQL插入语句
        placeholders = ', '.join(['%s'] * len(column_names))
        columns = ', '.join([f"`{col}`" for col in column_names])
        insert_sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        
        # 将Row对象转换为元组
        data_tuples = [tuple(row) for row in rows]
        
        # 插入到MySQL
        with mysql_engine.connect() as mysql_conn:
            # 清空目标表（可选）
            mysql_conn.execute(text(f"DELETE FROM `{table_name}`"))
            
            # 批量插入数据
            mysql_conn.execute(text(insert_sql), data_tuples)
            mysql_conn.commit()
        
        logger.info(f"表 {table_name} 迁移完成，共迁移 {len(data_tuples)} 条记录")
        
    except Exception as e:
        logger.error(f"迁移表 {table_name} 失败: {str(e)}")
        raise
    
    finally:
        sqlite_conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("SQLite到MySQL数据迁移脚本")
    print("=" * 60)
    
    try:
        # 查找SQLite数据库
        sqlite_path = find_sqlite_db()
        logger.info(f"找到SQLite数据库: {sqlite_path}")
        
        # 创建MySQL引擎
        mysql_engine = create_engine(settings.DATABASE_URL)
        logger.info(f"连接到MySQL: {settings.DATABASE_URL}")
        
        # 测试MySQL连接
        with mysql_engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            logger.info(f"MySQL版本: {version}")
        
        # 获取SQLite表列表
        tables = get_sqlite_tables(sqlite_path)
        logger.info(f"发现 {len(tables)} 个表: {', '.join(tables)}")
        
        # 确认是否继续
        response = input(f"\n是否继续迁移数据到MySQL？这将清空现有MySQL表中的数据。(y/N): ")
        if response.lower() != 'y':
            logger.info("迁移已取消")
            return
        
        # 迁移每个表
        success_count = 0
        for table in tables:
            try:
                migrate_table_data(sqlite_path, table, mysql_engine)
                success_count += 1
            except Exception as e:
                logger.error(f"跳过表 {table}: {str(e)}")
                continue
        
        print()
        print("=" * 60)
        print(f"✅ 数据迁移完成!")
        print(f"成功迁移 {success_count}/{len(tables)} 个表")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()