"""
数据库迁移CLI命令

与FastAPI架构集成的数据库迁移命令行工具
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings  # noqa: E402
from app.core.migrations import (  # noqa: E402
    MigrationError,
    data_seeder,
    migration_manager,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def migration():
    """数据库迁移管理命令"""
    pass


@migration.command(name="create")
@click.option("--message", "-m", required=True, help="迁移描述信息")
@click.option("--autogenerate/--no-autogenerate", default=True, help="是否自动生成迁移")
def create_migration_command(message: str, autogenerate: bool):
    """创建新的数据库迁移"""
    try:
        click.echo(f"🔄 创建迁移: {message}")
        click.echo(f"自动生成: {'是' if autogenerate else '否'}")

        revision = migration_manager.create_migration(message, autogenerate)

        click.echo("✅ 迁移创建成功")
        click.echo(f"版本ID: {revision}")

        # 显示模式差异
        if autogenerate:
            diff = migration_manager.get_schema_diff()
            if diff.get("has_changes"):
                click.echo(f"检测到 {diff['change_count']} 个变更")
                for change in diff["changes"][:5]:  # 只显示前5个变更
                    click.echo(f"  - {change}")
                if diff["change_count"] > 5:
                    click.echo(f"  ... 还有 {diff['change_count'] - 5} 个变更")
            else:
                click.echo("⚠️  未检测到模式变更")

    except MigrationError as e:
        click.echo(f"❌ 迁移创建失败: {e}", err=True)
        sys.exit(1)


@migration.command()
@click.option("--revision", "-r", default="head", help="目标版本，默认为最新版本")
@click.option("--backup/--no-backup", default=True, help="升级前是否备份数据库")
@click.option("--validate/--no-validate", default=True, help="是否验证迁移文件")
def upgrade(revision: str, backup: bool, validate: bool):
    """升级数据库到指定版本"""
    try:
        click.echo(f"🔄 升级数据库到版本: {revision}")

        # 检查当前状态
        status = migration_manager.check_migration_status()
        click.echo(f"当前版本: {status['current_revision']}")
        click.echo(
            f"目标版本: {status['head_revision'] if revision == 'head' else revision}"
        )

        if not status["needs_upgrade"] and revision == "head":
            click.echo("✅ 数据库已是最新版本")
            return

        # 验证迁移文件
        if validate:
            click.echo("🔍 验证迁移文件...")
            validation = migration_manager.validate_migrations()
            if not validation["valid"]:
                click.echo("❌ 迁移文件验证失败:")
                for error in validation["errors"]:
                    click.echo(f"  - {error}")
                sys.exit(1)

            if validation["warnings"]:
                click.echo("⚠️  迁移文件警告:")
                for warning in validation["warnings"]:
                    click.echo(f"  - {warning}")

        # 备份数据库
        if backup and "mysql" in settings.DATABASE_URL:
            click.echo("💾 创建数据库备份...")
            backup_file = migration_manager.backup_before_migration()
            if backup_file:
                click.echo(f"✅ 备份成功: {backup_file}")
            else:
                click.echo("⚠️  备份失败，但继续执行迁移")

        # 确认升级
        if not click.confirm("确认升级数据库吗？"):
            click.echo("操作已取消")
            return

        # 执行升级
        migration_manager.upgrade(revision)
        click.echo("✅ 数据库升级成功")

        # 显示新状态
        new_status = migration_manager.check_migration_status()
        click.echo(f"新版本: {new_status['current_revision']}")

    except MigrationError as e:
        click.echo(f"❌ 数据库升级失败: {e}", err=True)
        sys.exit(1)


@migration.command()
@click.option("--revision", "-r", required=True, help="目标版本")
@click.option("--backup/--no-backup", default=True, help="降级前是否备份数据库")
def downgrade(revision: str, backup: bool):
    """降级数据库到指定版本"""
    try:
        click.echo(f"🔄 降级数据库到版本: {revision}")

        # 检查当前状态
        status = migration_manager.check_migration_status()
        click.echo(f"当前版本: {status['current_revision']}")

        # 警告信息
        click.echo("⚠️  警告: 数据库降级可能导致数据丢失!")

        # 备份数据库
        if backup and "mysql" in settings.DATABASE_URL:
            click.echo("💾 创建数据库备份...")
            backup_file = migration_manager.backup_before_migration()
            if backup_file:
                click.echo(f"✅ 备份成功: {backup_file}")
            else:
                click.echo("❌ 备份失败")
                if not click.confirm("备份失败，是否继续降级？"):
                    sys.exit(1)

        # 确认降级
        if not click.confirm("确认降级数据库吗？这可能导致数据丢失!"):
            click.echo("操作已取消")
            return

        # 执行降级
        migration_manager.downgrade(revision)
        click.echo("✅ 数据库降级成功")

        # 显示新状态
        new_status = migration_manager.check_migration_status()
        click.echo(f"新版本: {new_status['current_revision']}")

    except MigrationError as e:
        click.echo(f"❌ 数据库降级失败: {e}", err=True)
        sys.exit(1)


@migration.command()
def status():
    """显示数据库迁移状态"""
    try:
        click.echo("📊 数据库迁移状态")
        click.echo("=" * 50)

        status = migration_manager.check_migration_status()

        click.echo(f"数据库URL: {settings.DATABASE_URL}")
        click.echo(f"数据库存在: {'✅' if status['database_exists'] else '❌'}")
        click.echo(f"当前版本: {status['current_revision'] or '未初始化'}")
        click.echo(f"最新版本: {status['head_revision'] or '无迁移文件'}")
        click.echo(f"状态: {'✅ 最新' if status['is_up_to_date'] else '⚠️  需要升级'}")

        if status.get("pending_migrations"):
            click.echo(f"待应用迁移: {status['pending_count']} 个")
            for migration in status["pending_migrations"][:5]:
                click.echo(f"  - {migration}")
            if status["pending_count"] > 5:
                click.echo(f"  ... 还有 {status['pending_count'] - 5} 个")

        # 显示模式差异
        diff = migration_manager.get_schema_diff()
        if diff.get("has_changes"):
            click.echo(f"未提交变更: {diff['change_count']} 个")
            click.echo("💡 提示: 运行 'migration create' 创建新迁移")

    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}", err=True)


@migration.command()
def history():
    """显示迁移历史"""
    try:
        click.echo("📜 迁移历史")
        click.echo("=" * 80)

        history = migration_manager.get_migration_history()
        current = migration_manager.get_current_revision()

        if not history:
            click.echo("无迁移历史")
            return

        for migration in history:
            is_current = migration["revision"] == current
            status_icon = "👉" if is_current else "  "

            click.echo(f"{status_icon} {migration['revision']}")
            click.echo(f"   消息: {migration['message'] or '无描述'}")
            click.echo(f"   上级: {migration['down_revision'] or '无'}")
            if migration.get("create_date"):
                click.echo(f"   日期: {migration['create_date']}")
            click.echo()

    except Exception as e:
        click.echo(f"❌ 获取历史失败: {e}", err=True)


@migration.command()
def validate():
    """验证迁移文件完整性"""
    try:
        click.echo("🔍 验证迁移文件...")

        validation = migration_manager.validate_migrations()

        if validation["valid"]:
            click.echo("✅ 所有迁移文件验证通过")
        else:
            click.echo("❌ 迁移文件验证失败:")
            for error in validation["errors"]:
                click.echo(f"  - {error}")

        if validation["warnings"]:
            click.echo("⚠️  警告:")
            for warning in validation["warnings"]:
                click.echo(f"  - {warning}")

        # 检查模式差异
        diff = migration_manager.get_schema_diff()
        if diff.get("has_changes"):
            click.echo(f"⚠️  检测到 {diff['change_count']} 个未提交的模式变更")
            click.echo("💡 建议运行 'migration create' 创建新迁移")

    except Exception as e:
        click.echo(f"❌ 验证失败: {e}", err=True)


@migration.command()
@click.option("--revision", "-r", required=True, help="要标记的版本")
def stamp(revision: str):
    """标记数据库版本（不执行迁移）"""
    try:
        click.echo(f"🏷️  标记数据库版本: {revision}")

        if not click.confirm("确认标记版本吗？这不会执行实际的迁移操作"):
            click.echo("操作已取消")
            return

        migration_manager.stamp(revision)
        click.echo(f"✅ 版本标记成功: {revision}")

    except MigrationError as e:
        click.echo(f"❌ 版本标记失败: {e}", err=True)
        sys.exit(1)


# 数据种子命令
@click.group()
def seed():
    """数据种子管理命令"""
    pass


@seed.command(name="create")
@click.option("--name", "-n", required=True, help="种子名称")
def create_seed_command(name: str):
    """创建数据种子文件"""
    try:
        click.echo(f"🌱 创建种子文件: {name}")

        seed_file = data_seeder.create_seed_file(name)
        click.echo(f"✅ 种子文件创建成功: {seed_file}")
        click.echo("💡 请编辑文件添加种子数据")

    except Exception as e:
        click.echo(f"❌ 种子文件创建失败: {e}", err=True)
        sys.exit(1)


@seed.command()
@click.option("--name", "-n", help="指定种子名称")
@click.option("--all", "run_all", is_flag=True, help="运行所有种子")
def run(name: Optional[str], run_all: bool):
    """运行数据种子"""
    try:
        if run_all:
            click.echo("🌱 运行所有种子...")
            count = data_seeder.run_all_seeds()
            click.echo(f"✅ 成功运行 {count} 个种子")
        elif name:
            click.echo(f"🌱 运行种子: {name}")
            data_seeder.run_seed(name)
            click.echo(f"✅ 种子运行成功: {name}")
        else:
            click.echo("❌ 请指定种子名称或使用 --all 运行所有种子")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 种子运行失败: {e}", err=True)
        sys.exit(1)


# 主命令组
@click.group()
def cli():
    """AI Video Studio 数据库管理工具"""
    pass


cli.add_command(migration)
cli.add_command(seed)

if __name__ == "__main__":
    cli()
