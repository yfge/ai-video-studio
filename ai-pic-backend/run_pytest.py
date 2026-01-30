#!/usr/bin/env python3
"""
pytest运行脚本

提供多种测试运行选项和便捷命令
"""

import argparse
import subprocess
import sys
from pathlib import Path


class PytestRunner:
    """pytest运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent

    def run_command(self, cmd, description=None):
        """运行命令并显示结果"""
        if description:
            print(f"\n🚀 {description}")
            print("=" * 50)

        print(f"执行命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            return result.returncode == 0
        except KeyboardInterrupt:
            print("\n⏹️  测试被用户中断")
            return False
        except Exception as e:
            print(f"❌ 命令执行失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        cmd = ["python", "-m", "pytest"]
        return self.run_command(cmd, "运行所有测试")

    def run_unit_tests(self):
        """运行单元测试"""
        cmd = ["python", "-m", "pytest", "-m", "unit"]
        return self.run_command(cmd, "运行单元测试")

    def run_integration_tests(self):
        """运行集成测试"""
        cmd = ["python", "-m", "pytest", "-m", "integration"]
        return self.run_command(cmd, "运行集成测试")

    def run_diagnostic_tests(self):
        """运行诊断测试"""
        cmd = ["python", "-m", "pytest", "-m", "diagnostic", "-v"]
        return self.run_command(cmd, "运行诊断测试")

    def run_api_tests(self):
        """运行API测试"""
        cmd = ["python", "-m", "pytest", "-m", "api", "-v"]
        return self.run_command(cmd, "运行API测试")

    def run_external_tests(self):
        """运行外部服务测试"""
        cmd = ["python", "-m", "pytest", "-m", "external", "-v", "-s"]
        return self.run_command(cmd, "运行外部服务测试（需要API密钥）")

    def run_quick_tests(self):
        """运行快速测试（跳过慢速和外部测试）"""
        cmd = ["python", "-m", "pytest", "-m", "not slow and not external"]
        return self.run_command(cmd, "运行快速测试")

    def run_coverage_tests(self):
        """运行覆盖率测试"""
        cmd = ["python", "-m", "pytest", "--cov-report=html", "--cov-report=term"]
        success = self.run_command(cmd, "运行覆盖率测试")

        if success:
            print("\n📊 覆盖率报告已生成:")
            print("  HTML报告: htmlcov/index.html")
            print("  打开命令: open htmlcov/index.html")

        return success

    def run_specific_test(self, test_path):
        """运行特定测试"""
        cmd = ["python", "-m", "pytest", test_path, "-v"]
        return self.run_command(cmd, f"运行特定测试: {test_path}")

    def check_environment(self):
        """检查测试环境"""
        print("🔍 检查测试环境...")

        # 检查pytest是否安装
        try:
            import pytest

            print(f"✅ pytest版本: {pytest.__version__}")
        except ImportError:
            print("❌ pytest未安装")
            return False

        # 检查测试目录
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            print(f"✅ 测试目录存在: {tests_dir}")
        else:
            print(f"❌ 测试目录不存在: {tests_dir}")
            return False

        # 检查配置文件
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            print(f"✅ pytest配置文件存在: {pytest_ini}")
        else:
            print(f"⚠️  pytest配置文件不存在: {pytest_ini}")

        # 检查依赖
        required_packages = ["pytest-asyncio", "pytest-cov"]
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package} 已安装")
            except ImportError:
                print(f"❌ {package} 未安装")
                print(f"   安装命令: pip install {package}")

        print("✅ 环境检查完成")
        return True

    def show_test_info(self):
        """显示测试信息"""
        cmd = ["python", "-m", "pytest", "--collect-only", "-q"]
        self.run_command(cmd, "收集测试信息")

    def run_failed_tests(self):
        """重新运行失败的测试"""
        cmd = ["python", "-m", "pytest", "--lf", "-v"]
        return self.run_command(cmd, "重新运行失败的测试")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="pytest测试运行器")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--diagnostic", action="store_true", help="运行诊断测试")
    parser.add_argument("--api", action="store_true", help="运行API测试")
    parser.add_argument("--external", action="store_true", help="运行外部服务测试")
    parser.add_argument("--quick", action="store_true", help="运行快速测试")
    parser.add_argument("--coverage", action="store_true", help="运行覆盖率测试")
    parser.add_argument("--failed", action="store_true", help="重新运行失败的测试")
    parser.add_argument("--info", action="store_true", help="显示测试信息")
    parser.add_argument("--check", action="store_true", help="检查测试环境")
    parser.add_argument("--test", type=str, help="运行特定测试文件或函数")

    args = parser.parse_args()

    runner = PytestRunner()

    # 如果没有指定任何选项，显示帮助
    if not any(vars(args).values()):
        print("🧪 pytest测试运行器")
        print("=" * 50)
        print("使用 --help 查看所有选项")
        print("\n常用命令:")
        print("  --check      检查测试环境")
        print("  --diagnostic 运行诊断测试")
        print("  --quick      运行快速测试")
        print("  --all        运行所有测试")
        print("  --coverage   运行覆盖率测试")
        return

    success = True

    if args.check:
        success &= runner.check_environment()

    if args.info:
        runner.show_test_info()

    if args.unit:
        success &= runner.run_unit_tests()

    if args.integration:
        success &= runner.run_integration_tests()

    if args.diagnostic:
        success &= runner.run_diagnostic_tests()

    if args.api:
        success &= runner.run_api_tests()

    if args.external:
        success &= runner.run_external_tests()

    if args.quick:
        success &= runner.run_quick_tests()

    if args.coverage:
        success &= runner.run_coverage_tests()

    if args.failed:
        success &= runner.run_failed_tests()

    if args.test:
        success &= runner.run_specific_test(args.test)

    if args.all:
        success &= runner.run_all_tests()

    # 显示最终结果
    if success:
        print("\n🎉 测试完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
