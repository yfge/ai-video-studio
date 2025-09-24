#!/usr/bin/env python3
"""
AI图像生成自动化测试脚本

独立运行的测试脚本，无需启动FastAPI服务器
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.services.diagnostic_service import DiagnosticService


async def main():
    """主测试函数"""
    print("🚀 AI图像生成自动化测试脚本")
    print("=" * 50)
    
    diagnostic = DiagnosticService()
    
    # 运行完整诊断
    print("\n📋 运行完整诊断测试...")
    result = await diagnostic.run_full_diagnostic()
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 诊断结果总结")
    print("=" * 50)
    
    summary = result["summary"]
    print(f"总体状态: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}")
    print(f"测试总数: {summary['total_tests']}")
    print(f"通过测试: {summary['passed_tests']}")
    print(f"失败测试: {summary['failed_tests']}")
    print(f"成功率: {summary['success_rate']}")
    
    # 显示详细结果
    print(f"\n📝 详细测试结果:")
    for test_name, test_result in result["test_results"].items():
        status = "✅" if test_result["success"] else "❌"
        print(f"{status} {test_name}")
        if test_result["details"]:
            # 缩进显示详细信息
            for line in test_result["details"].split('\n'):
                if line.strip():
                    print(f"    {line.strip()}")
        if test_result["error"]:
            print(f"    错误: {test_result['error']}")
    
    # 显示错误列表
    if result["errors"]:
        print(f"\n❌ 发现的问题:")
        for error in result["errors"]:
            print(f"  • {error}")
    
    # 显示建议
    if result["recommendations"]:
        print(f"\n🔧 修复建议:")
        for rec in result["recommendations"]:
            print(f"  {rec}")
    
    # 保存完整报告到文件
    report_file = "diagnostic_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 完整报告已保存到: {report_file}")
    
    # 如果有错误，退出码为1
    if result["errors"]:
        print(f"\n❌ 测试完成，发现 {len(result['errors'])} 个问题")
        sys.exit(1)
    else:
        print(f"\n🎉 测试完成，所有功能正常！")
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试脚本异常: {e}")
        sys.exit(1)