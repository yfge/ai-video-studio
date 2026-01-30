#!/usr/bin/env python3
"""
数据库迁移管理脚本

使用方法:
    python migrate.py init          # 初始化迁移（仅第一次使用）
    python migrate.py generate      # 生成新的迁移文件
    python migrate.py upgrade       # 应用迁移到数据库
    python migrate.py downgrade     # 回退迁移
    python migrate.py current       # 查看当前迁移版本
    python migrate.py history       # 查看迁移历史
    python migrate.py reset         # 重置数据库（危险操作）
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"错误: {result.stderr}")
            return False
        if result.stdout:
            print(result.stdout)
        return True
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False


def init_migration():
    """初始化迁移"""
    print("正在初始化数据库迁移...")
    if not run_command("alembic stamp head"):
        print("初始化失败")
        return False
    print("迁移初始化完成")
    return True


def generate_migration():
    """生成新的迁移文件"""
    message = input("请输入迁移描述信息 (可选): ").strip()
    if message:
        cmd = f'alembic revision --autogenerate -m "{message}"'
    else:
        cmd = "alembic revision --autogenerate"

    print("正在生成迁移文件...")
    if not run_command(cmd):
        print("生成迁移文件失败")
        return False
    print("迁移文件生成完成")
    return True


def upgrade_database():
    """应用迁移到数据库"""
    print("正在应用迁移到数据库...")
    if not run_command("alembic upgrade head"):
        print("应用迁移失败")
        return False
    print("迁移应用完成")
    return True


def downgrade_database():
    """回退迁移"""
    print("警告: 这将回退数据库到上一个版本！")
    confirm = input("确定要继续吗? (y/N): ").strip().lower()
    if confirm != "y":
        print("操作已取消")
        return False

    print("正在回退迁移...")
    if not run_command("alembic downgrade -1"):
        print("回退迁移失败")
        return False
    print("迁移回退完成")
    return True


def show_current():
    """显示当前迁移版本"""
    print("当前迁移版本:")
    run_command("alembic current")


def show_history():
    """显示迁移历史"""
    print("迁移历史:")
    run_command("alembic history")


def reset_database():
    """重置数据库（危险操作）"""
    print("警告: 这将删除所有数据并重置数据库！")
    confirm = input("确定要继续吗? (y/N): ").strip().lower()
    if confirm != "y":
        print("操作已取消")
        return False

    double_confirm = input("再次确认，这将删除所有数据！输入 'RESET' 确认: ").strip()
    if double_confirm != "RESET":
        print("操作已取消")
        return False

    print("正在重置数据库...")
    # 回退到初始状态
    if not run_command("alembic downgrade base"):
        print("重置失败")
        return False

    # 重新应用所有迁移
    if not run_command("alembic upgrade head"):
        print("重新应用迁移失败")
        return False

    print("数据库重置完成")
    return True


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    # 确保在正确的目录中
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    commands = {
        "init": init_migration,
        "generate": generate_migration,
        "upgrade": upgrade_database,
        "downgrade": downgrade_database,
        "current": show_current,
        "history": show_history,
        "reset": reset_database,
    }

    if command not in commands:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)

    try:
        commands[command]()
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"执行命令时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
