#!/usr/bin/env python3
"""
MySQL数据库迁移管理脚本

提供数据库创建、迁移、回滚等功能
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_command(cmd: str, description: str = "") -> bool:
    """运行命令并返回结果"""
    if description:
        print(f"\n{'='*60}")
        print(f"🔄 {description}")
        print(f"{'='*60}")

    print(f"执行命令: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(f"错误输出: {result.stderr}")

        if result.returncode != 0:
            print(f"❌ 命令执行失败，退出码: {result.returncode}")
            return False
        else:
            print("✅ 命令执行成功")
            return True

    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False


def init_database():
    """初始化数据库"""
    try:
        print("=" * 60)
        print("初始化MySQL数据库")
        print("=" * 60)

        # 运行数据库初始化脚本
        if not os.path.exists("scripts/init_mysql_db.py"):
            print("❌ 找不到数据库初始化脚本")
            return False

        return run_command("python scripts/init_mysql_db.py", "初始化数据库")

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False


def create_migration(message: str):
    """创建新的迁移文件"""
    if not message:
        print("❌ 请提供迁移消息")
        return False

    cmd = f'alembic revision --autogenerate -m "{message}"'
    return run_command(cmd, f"创建迁移: {message}")


def upgrade_database(revision: str = "head"):
    """升级数据库到指定版本"""
    cmd = f"alembic upgrade {revision}"
    return run_command(cmd, f"升级数据库到版本: {revision}")


def downgrade_database(revision: str):
    """降级数据库到指定版本"""
    if not revision:
        print("❌ 请提供要降级到的版本")
        return False

    cmd = f"alembic downgrade {revision}"
    return run_command(cmd, f"降级数据库到版本: {revision}")


def show_current_revision():
    """显示当前数据库版本"""
    return run_command("alembic current", "显示当前数据库版本")


def show_migration_history():
    """显示迁移历史"""
    return run_command("alembic history", "显示迁移历史")


def show_migration_heads():
    """显示迁移头"""
    return run_command("alembic heads", "显示迁移头")


def test_connection():
    """测试数据库连接"""
    if not os.path.exists("test_mysql_connection.py"):
        print("❌ 找不到数据库连接测试脚本")
        return False

    return run_command("python test_mysql_connection.py", "测试数据库连接")


def migrate_from_sqlite():
    """从SQLite迁移数据"""
    if not os.path.exists("scripts/migrate_to_mysql.py"):
        print("❌ 找不到SQLite迁移脚本")
        return False

    return run_command("python scripts/migrate_to_mysql.py", "从SQLite迁移数据")


def reset_database():
    """重置数据库（危险操作）"""
    response = input("⚠️  这将删除所有数据并重新创建表结构，确定要继续吗？(y/N): ")
    if response.lower() != "y":
        print("操作已取消")
        return False

    success = True

    # 降级到base
    if not downgrade_database("base"):
        success = False

    # 重新升级到head
    if success and not upgrade_database("head"):
        success = False

    return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MySQL数据库迁移管理脚本")
    parser.add_argument(
        "command",
        choices=[
            "init",
            "create",
            "upgrade",
            "downgrade",
            "current",
            "history",
            "heads",
            "test",
            "migrate",
            "reset",
        ],
        help="要执行的命令",
    )
    parser.add_argument("--message", "-m", help="迁移消息（用于create命令）")
    parser.add_argument(
        "--revision", "-r", help="目标版本（用于upgrade/downgrade命令）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MySQL数据库迁移管理")
    print("=" * 60)
    print(f"项目目录: {project_root}")
    print(f"执行命令: {args.command}")
    print()

    success = True

    if args.command == "init":
        success = init_database()
    elif args.command == "create":
        if not args.message:
            print("❌ 创建迁移需要提供消息，使用 --message 或 -m 参数")
            success = False
        else:
            success = create_migration(args.message)
    elif args.command == "upgrade":
        revision = args.revision or "head"
        success = upgrade_database(revision)
    elif args.command == "downgrade":
        if not args.revision:
            print("❌ 降级需要提供目标版本，使用 --revision 或 -r 参数")
            success = False
        else:
            success = downgrade_database(args.revision)
    elif args.command == "current":
        success = show_current_revision()
    elif args.command == "history":
        success = show_migration_history()
    elif args.command == "heads":
        success = show_migration_heads()
    elif args.command == "test":
        success = test_connection()
    elif args.command == "migrate":
        success = migrate_from_sqlite()
    elif args.command == "reset":
        success = reset_database()

    if success:
        print("\n🎉 操作执行成功!")
        sys.exit(0)
    else:
        print("\n❌ 操作执行失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
