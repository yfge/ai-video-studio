#!/usr/bin/env python3
"""
测试可灵AI图像生成功能

由于可灵AI需要真实的API密钥，这个脚本使用模拟数据进行测试。
实际使用时需要配置真实的KELING_API_KEY和KELING_SECRET_KEY。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_service import AIService
from app.core.config import settings

async def test_keling_ai():
    """测试可灵AI图像生成功能"""
    
    print("🧪 测试可灵AI图像生成功能")
    print("=" * 50)
    
    # 检查环境变量配置
    if not settings.KELING_API_KEY or not settings.KELING_SECRET_KEY:
        print("❌ 可灵AI配置缺失:")
        print(f"   KELING_API_KEY: {'✅已配置' if settings.KELING_API_KEY else '❌未配置'}")
        print(f"   KELING_SECRET_KEY: {'✅已配置' if settings.KELING_SECRET_KEY else '❌未配置'}")
        print("")
        print("💡 要测试可灵AI，请在.env文件中配置:")
        print("   KELING_API_KEY=your-keling-api-key")
        print("   KELING_SECRET_KEY=your-keling-secret-key")
        print("")
        print("🔧 模拟测试模式:")
        print("   由于缺少真实API密钥，将运行模拟测试")
        await simulate_keling_test()
        return
    
    # 真实API测试
    print(f"✅ 可灵AI配置已找到")
    print(f"   API Key: {settings.KELING_API_KEY[:10]}...")
    print(f"   Secret Key: {settings.KELING_SECRET_KEY[:10]}...")
    print("")
    
    try:
        # 初始化AI服务
        ai_service = AIService()
        print("📦 AI服务初始化完成")
        
        # 检查AI管理器状态
        if not ai_service.ai_manager:
            print("❌ AI管理器未初始化")
            return
        
        print("📋 AI管理器状态:")
        provider_status = ai_service.ai_manager.get_provider_status()
        for provider_name, status in provider_status.items():
            if provider_name == "keling":
                print(f"   可灵AI: {'✅可用' if status.get('enabled') else '❌不可用'}")
        
        # 测试图像生成
        print("\n🎨 开始测试可灵AI图像生成...")
        
        test_cases = [
            {
                "prompt": "一个可爱的小女孩，卡通风格",
                "style": "cartoon",
                "model": "keling-kolors"
            },
            {
                "prompt": "现代都市风景，夜景",
                "style": "realistic", 
                "model": "kling-image"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}:")
            print(f"   提示词: {test_case['prompt']}")
            print(f"   风格: {test_case['style']}")
            print(f"   模型: {test_case['model']}")
            
            result = await ai_service.generate_virtual_ip_image(
                ip_name="测试角色",
                description="测试描述",
                style=test_case["style"],
                category="portrait",
                model=test_case["model"],
                additional_prompts=[test_case["prompt"]]
            )
            
            if result:
                print(f"   ✅ 生成成功!")
                print(f"   📁 文件路径: {result.get('local_file_path', 'N/A')}")
                print(f"   🌐 图像URL: {result.get('image_url', 'N/A')}")
                print(f"   📝 生成方法: {result.get('generation_method', 'N/A')}")
            else:
                print(f"   ❌ 生成失败")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def simulate_keling_test():
    """模拟可灵AI测试（当没有真实API密钥时）"""
    print("🎭 运行可灵AI模拟测试")
    print("")
    
    # 模拟可灵AI响应
    mock_response = {
        "success": True,
        "data": {
            "images": ["https://mock-keling-api.com/generated-image-123.png"]
        },
        "provider": "keling",
        "model": "keling-kolors",
        "metadata": {
            "width": 1024,
            "height": 1024,
            "style": "realistic",
            "prompt": "一个可爱的小女孩，充满好奇心"
        }
    }
    
    print("📊 模拟可灵AI响应:")
    print(f"   状态: {'✅成功' if mock_response['success'] else '❌失败'}")
    print(f"   提供商: {mock_response['provider']}")
    print(f"   模型: {mock_response['model']}")
    print(f"   图像数量: {len(mock_response['data']['images'])}")
    print(f"   图像URL: {mock_response['data']['images'][0]}")
    print("")
    
    # 模拟AI服务集成测试
    print("🔧 模拟AI服务集成:")
    try:
        ai_service = AIService()
        print(f"   AI管理器初始化: {'✅成功' if ai_service.ai_manager else '❌失败'}")
        
        if ai_service.ai_manager:
            # 检查可灵提供商是否在配置中
            from app.services.providers.keling_provider import KelingProvider
            print(f"   可灵提供商类: ✅已导入")
            print(f"   支持的模型类型: {KelingProvider.__doc__ or '视频和图像生成'}")
        
    except Exception as e:
        print(f"   ❌ 模拟测试失败: {e}")
    
    print("")
    print("💡 要进行真实测试，请:")
    print("   1. 注册可灵AI账号: https://klingai.com/")
    print("   2. 获取API密钥")
    print("   3. 在.env文件中配置KELING_API_KEY和KELING_SECRET_KEY")
    print("   4. 重新运行此测试脚本")


async def main():
    """主函数"""
    print("🚀 可灵AI图像生成测试脚本")
    print("📅 版本: 1.0")
    print("🎯 目标: 测试可灵AI集成功能")
    print("")
    
    await test_keling_ai()
    
    print("")
    print("✨ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())