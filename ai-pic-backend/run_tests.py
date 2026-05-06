#!/usr/bin/env python3
"""
测试运行脚本

使用方法:
    python run_tests.py                    # 运行所有测试
    python run_tests.py unit              # 只运行单元测试
    python run_tests.py integration       # 只运行集成测试
    python run_tests.py migration         # 只运行迁移测试
    python run_tests.py coverage          # 运行测试并生成覆盖率报告
    python run_tests.py quick             # 快速测试（跳过慢速测试）
    python run_tests.py parallel          # 并行运行测试
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
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


def setup_test_environment():
    """设置测试环境"""
    print("🔧 设置测试环境...")

    # 确保在正确的目录中
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 检查虚拟环境
    if not Path(".venv").exists():
        print("❌ 虚拟环境不存在，请先创建虚拟环境")
        return False

    # 安装测试依赖
    if not run_command("pip install -r requirements-test.txt", "安装测试依赖"):
        return False

    # 设置测试数据库
    setup_test_database_cmd = (
        'python -c "import importlib.util;'
        " name='app.core.test_database' if importlib.util.find_spec('app.core.test_database')"
        " else 'tests.unit.test_database';"
        " mod=__import__(name, fromlist=['setup_test_database']);"
        ' mod.setup_test_database()"'
    )
    if not run_command(setup_test_database_cmd, "设置测试数据库"):
        return False

    return True


def run_unit_tests():
    """运行单元测试"""
    cmd = "pytest tests/ -m unit -v"
    return run_command(cmd, "运行单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = "pytest tests/ -m integration -v"
    return run_command(cmd, "运行集成测试")


def run_migration_tests():
    """运行迁移测试"""
    cmd = "pytest tests/test_migrations.py -v"
    return run_command(cmd, "运行迁移测试")


def run_api_tests():
    """运行API测试"""
    cmd = "pytest tests/test_api.py -v"
    return run_command(cmd, "运行API测试")


def run_model_tests():
    """运行模型测试"""
    cmd = "pytest tests/test_models.py -v"
    return run_command(cmd, "运行模型测试")


def run_e2e_tests():
    """运行端到端测试"""
    cmd = "pytest tests/ -m e2e -v"
    return run_command(cmd, "运行端到端测试")


def run_all_tests():
    """运行所有测试"""
    cmd = "pytest tests/ -v"
    return run_command(cmd, "运行所有测试")


def run_quick_tests():
    """运行快速测试（跳过慢速测试）"""
    cmd = "pytest tests/ -m 'not slow' -v"
    return run_command(cmd, "运行快速测试")


def run_parallel_tests():
    """并行运行测试"""
    cmd = "pytest tests/ -n auto -v"
    return run_command(cmd, "并行运行测试")


def run_coverage_tests():
    """运行测试并生成覆盖率报告"""
    cmd = "pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml"
    success = run_command(cmd, "运行测试并生成覆盖率报告")

    if success:
        print("\n📊 覆盖率报告已生成:")
        print("  - HTML报告: htmlcov/index.html")
        print("  - XML报告: coverage.xml")
        print("  - 终端报告: 已显示在上方")

    return success


def run_specific_test(test_path):
    """运行特定测试"""
    cmd = f"pytest {test_path} -v"
    return run_command(cmd, f"运行特定测试: {test_path}")


def lint_code():
    """代码质量检查"""
    print("\n🔍 代码质量检查...")

    # 安装linting工具
    run_command("pip install flake8 black isort", "安装代码质量工具")

    # 运行flake8
    if not run_command(
        "flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503",
        "运行flake8检查",
    ):
        print("⚠️  flake8检查发现问题")

    # 运行black检查
    if not run_command("black --check app/ tests/", "运行black格式检查"):
        print("⚠️  black格式检查发现问题")
        print("💡 运行 'black app/ tests/' 自动格式化代码")

    # 运行isort检查
    if not run_command("isort --check-only app/ tests/", "运行isort导入检查"):
        print("⚠️  isort导入检查发现问题")
        print("💡 运行 'isort app/ tests/' 自动排序导入")


def clean_test_artifacts():
    """清理测试产物"""
    print("\n🧹 清理测试产物...")

    artifacts = [
        "htmlcov/",
        "coverage.xml",
        "test-results.xml",
        ".coverage",
        ".pytest_cache/",
        "__pycache__/",
        "*.pyc",
        "test.db",
        "test_*.db",
    ]

    for artifact in artifacts:
        if "*" in artifact:
            run_command(f"find . -name '{artifact}' -delete", f"删除 {artifact}")
        else:
            run_command(f"rm -rf {artifact}", f"删除 {artifact}")

    print("✅ 测试产物清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试运行脚本")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=[
            "all",
            "unit",
            "integration",
            "migration",
            "api",
            "model",
            "e2e",
            "coverage",
            "quick",
            "parallel",
            "lint",
            "clean",
            "setup",
        ],
        help="要运行的测试类型",
    )
    parser.add_argument("--test", "-t", help="运行特定测试文件或函数")
    parser.add_argument("--no-setup", action="store_true", help="跳过环境设置")

    args = parser.parse_args()

    # 设置测试环境
    if not args.no_setup and args.command != "clean":
        if not setup_test_environment():
            print("❌ 测试环境设置失败")
            sys.exit(1)

    # 执行相应的命令
    success = True

    if args.test:
        success = run_specific_test(args.test)
    elif args.command == "all":
        success = run_all_tests()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "migration":
        success = run_migration_tests()
    elif args.command == "api":
        success = run_api_tests()
    elif args.command == "model":
        success = run_model_tests()
    elif args.command == "e2e":
        success = run_e2e_tests()
    elif args.command == "coverage":
        success = run_coverage_tests()
    elif args.command == "quick":
        success = run_quick_tests()
    elif args.command == "parallel":
        success = run_parallel_tests()
    elif args.command == "lint":
        lint_code()
    elif args.command == "clean":
        clean_test_artifacts()
    elif args.command == "setup":
        success = setup_test_environment()

    if success:
        print("\n🎉 测试执行成功!")
        sys.exit(0)
    else:
        print("\n❌ 测试执行失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
