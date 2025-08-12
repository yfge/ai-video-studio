#!/usr/bin/env python3
"""
Django风格的管理脚本

提供统一的CLI接口来管理FastAPI应用
"""

import os
import sys
import click
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.cli.migration_commands import cli as migration_cli
from app.core.config import settings

@click.group(invoke_without_command=True)
@click.pass_context
def manage(ctx):
    """AI Video Studio 管理工具"""
    if ctx.invoked_subcommand is None:
        click.echo("🎬 AI Video Studio 管理工具")
        click.echo("=" * 50)
        click.echo(f"项目: {settings.PROJECT_NAME}")
        click.echo(f"版本: {settings.VERSION}")
        click.echo(f"数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
        click.echo()
        click.echo("可用命令:")
        click.echo("  migration  - 数据库迁移管理")
        click.echo("  seed      - 数据种子管理")
        click.echo("  server    - 服务器管理")
        click.echo("  dev       - 开发工具")
        click.echo()
        click.echo("使用 'python manage.py <命令> --help' 查看详细帮助")

# 添加迁移命令组
from app.cli.migration_commands import migration, seed
manage.add_command(migration)
manage.add_command(seed)

# 服务器管理命令
@manage.group()
def server():
    """服务器管理命令"""
    pass

@server.command()
@click.option('--host', default='0.0.0.0', help='服务器主机地址')
@click.option('--port', default=8000, help='服务器端口')
@click.option('--reload/--no-reload', default=True, help='是否启用热重载')
@click.option('--workers', default=1, help='工作进程数')
def run(host: str, port: int, reload: bool, workers: int):
    """启动开发服务器"""
    import uvicorn
    
    click.echo(f"🚀 启动服务器: http://{host}:{port}")
    click.echo(f"热重载: {'启用' if reload else '禁用'}")
    click.echo(f"工作进程: {workers}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        log_level="info"
    )

@server.command()
@click.option('--host', default='0.0.0.0', help='服务器主机地址')
@click.option('--port', default=8000, help='服务器端口')
@click.option('--workers', default=4, help='工作进程数')
def production(host: str, port: int, workers: int):
    """启动生产服务器"""
    import uvicorn
    
    click.echo(f"🏭 启动生产服务器: http://{host}:{port}")
    click.echo(f"工作进程: {workers}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="warning",
        access_log=True
    )

# 开发工具命令
@manage.group()
def dev():
    """开发工具命令"""
    pass

@dev.command()
def check():
    """检查项目配置和依赖"""
    click.echo("🔍 检查项目配置...")
    
    issues = []
    
    # 检查环境变量
    if settings.SECRET_KEY == "your-secret-key-here":
        issues.append("⚠️  SECRET_KEY 使用默认值，请修改")
    
    # 检查数据库连接
    try:
        from app.core.migrations import migration_manager
        status = migration_manager.check_migration_status()
        if not status['database_exists']:
            issues.append("❌ 数据库连接失败")
        elif not status['is_up_to_date']:
            issues.append("⚠️  数据库需要升级")
        else:
            click.echo("✅ 数据库连接正常")
    except Exception as e:
        issues.append(f"❌ 数据库检查失败: {e}")
    
    # 检查依赖文件
    required_files = [
        "requirements.txt",
        "alembic.ini",
        "app/core/config.py",
        "app/models/__init__.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"❌ 缺少文件: {file_path}")
    
    # 检查目录结构
    required_dirs = [
        "app/api",
        "app/core",
        "app/models",
        "alembic/versions"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"❌ 缺少目录: {dir_path}")
    
    if issues:
        click.echo("\n发现以下问题:")
        for issue in issues:
            click.echo(f"  {issue}")
        click.echo(f"\n共发现 {len(issues)} 个问题")
    else:
        click.echo("✅ 项目配置检查通过")

@dev.command()
def test():
    """运行测试"""
    import subprocess
    
    click.echo("🧪 运行测试...")
    
    try:
        result = subprocess.run([
            sys.executable, "run_tests.py", "quick"
        ], capture_output=True, text=True)
        
        click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr)
        
        if result.returncode == 0:
            click.echo("✅ 测试通过")
        else:
            click.echo("❌ 测试失败")
            sys.exit(1)
            
    except FileNotFoundError:
        click.echo("❌ 找不到测试脚本 run_tests.py")
        sys.exit(1)

@dev.command()
def lint():
    """代码质量检查"""
    import subprocess
    
    click.echo("🔍 代码质量检查...")
    
    commands = [
        ("flake8", ["flake8", "app/", "--max-line-length=88", "--extend-ignore=E203,W503"]),
        ("black", ["black", "--check", "app/"]),
        ("isort", ["isort", "--check-only", "app/"])
    ]
    
    all_passed = True
    
    for name, cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                click.echo(f"✅ {name} 检查通过")
            else:
                click.echo(f"❌ {name} 检查失败:")
                click.echo(result.stdout)
                all_passed = False
        except FileNotFoundError:
            click.echo(f"⚠️  {name} 未安装，跳过检查")
    
    if all_passed:
        click.echo("✅ 所有代码质量检查通过")
    else:
        click.echo("❌ 代码质量检查有问题，请修复后重试")
        sys.exit(1)

@dev.command()
def format():
    """格式化代码"""
    import subprocess
    
    click.echo("🎨 格式化代码...")
    
    commands = [
        ("isort", ["isort", "app/"]),
        ("black", ["black", "app/"])
    ]
    
    for name, cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                click.echo(f"✅ {name} 格式化完成")
            else:
                click.echo(f"❌ {name} 格式化失败:")
                click.echo(result.stderr)
        except FileNotFoundError:
            click.echo(f"⚠️  {name} 未安装，跳过格式化")

@dev.command()
def shell():
    """启动交互式Python shell"""
    import code
    
    # 导入常用模块
    import sys
    sys.path.insert(0, str(project_root))
    
    from app.core.database import SessionLocal, engine
    from app.core.config import settings
    import app.models
    
    click.echo("🐍 启动Python shell...")
    click.echo("已导入的模块:")
    click.echo("  - SessionLocal, engine (数据库)")
    click.echo("  - settings (配置)")
    click.echo("  - 所有模型 (from app.models import *)")
    click.echo()
    
    # 创建数据库会话
    db = SessionLocal()
    
    # 启动交互式shell
    code.interact(
        banner="AI Video Studio 开发Shell",
        local={
            "db": db,
            "engine": engine,
            "settings": settings,
            "models": app.models
        }
    )

# 快捷命令
@manage.command()
def quickstart():
    """快速启动项目"""
    click.echo("🚀 快速启动项目...")
    
    # 检查数据库
    try:
        from app.core.migrations import migration_manager
        status = migration_manager.check_migration_status()
        
        if not status['database_exists']:
            click.echo("📦 初始化数据库...")
            if click.confirm("数据库不存在，是否创建？"):
                # 这里可以调用数据库初始化脚本
                pass
        
        if not status['is_up_to_date']:
            click.echo("🔄 升级数据库...")
            if click.confirm("数据库需要升级，是否升级？"):
                migration_manager.upgrade()
        
    except Exception as e:
        click.echo(f"❌ 数据库检查失败: {e}")
        return
    
    # 启动服务器
    click.echo("🚀 启动开发服务器...")
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == '__main__':
    manage()