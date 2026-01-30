#!/usr/bin/env python3
"""
测试修复后的可灵AI图像生成功能

这个脚本会测试：
1. 可灵AI提供商的初始化
2. 重试机制是否生效
3. 服务繁忙时的处理
4. AI服务管理器的集成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.ai_service import AIService


async def test_keling_with_retries():
    """测试可灵AI的重试机制"""

    print("🚀 测试修复后的可灵AI图像生成功能")
    print("=" * 60)

    # 检查环境变量配置
    if not settings.KELING_API_KEY or not settings.KELING_SECRET_KEY:
        print("❌ 可灵AI配置缺失")
        print(
            f"   KELING_API_KEY: {'✅已配置' if settings.KELING_API_KEY else '❌未配置'}"
        )
        print(
            f"   KELING_SECRET_KEY: {'✅已配置' if settings.KELING_SECRET_KEY else '❌未配置'}"
        )
        return

    print("✅ 可灵AI配置检查通过")
    print(f"   API Key: {settings.KELING_API_KEY[:10]}...****")
    print(f"   Secret Key: {settings.KELING_SECRET_KEY[:10]}...****")
    print()

    try:
        # 初始化AI服务
        ai_service = AIService()
        print("📦 AI服务初始化完成")

        # 检查AI管理器状态
        if not ai_service.ai_manager:
            print("❌ AI管理器未初始化")
            return

        print("🤖 AI管理器状态:")
        try:
            provider_status = ai_service.ai_manager.get_provider_status()
            for provider_name, status in provider_status.items():
                if provider_name == "keling":
                    print(
                        f"   可灵AI: {'✅可用' if status.get('enabled') else '❌不可用'}"
                    )
                    print(f"   配置详情: {status}")
        except Exception as e:
            print(f"   状态获取失败: {e}")
        print()

        # 测试用例
        test_cases = [
            {
                "name": "基础测试",
                "prompt": "一个可爱的小女孩，卡通风格，高质量",
                "style": "cartoon",
                "model": "kling-image",
            },
            {
                "name": "现实风格测试",
                "prompt": "现代都市风景，夜景，霓虹灯",
                "style": "realistic",
                "model": "kling-image",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"🎨 测试用例 {i}: {test_case['name']}")
            print(f"   提示词: {test_case['prompt']}")
            print(f"   风格: {test_case['style']}")
            print(f"   模型: {test_case['model']}")
            print("   开始调用可灵AI...")

            try:
                # 使用AI管理器直接调用
                response = await ai_service.ai_manager.generate_image(
                    prompt=test_case["prompt"],
                    width=1024,
                    height=1024,
                    style=test_case["style"],
                    model=test_case["model"],
                    prefer_provider="keling",
                )

                print("   📊 响应结果:")
                print(f"     成功: {'✅' if response.success else '❌'}")
                print(f"     提供商: {response.provider}")
                print(f"     模型: {response.model}")

                if response.success:
                    print("     ✅ 生成成功!")
                    if response.data and "images" in response.data:
                        images = response.data["images"]
                        print(f"     生成图像数量: {len(images)}")
                        for j, img_url in enumerate(images):
                            print(f"     图像 {j+1}: {str(img_url)[:100]}...")
                    else:
                        print(f"     数据: {response.data}")
                else:
                    print(f"     ❌ 生成失败: {response.error}")

                print(f"     元数据: {response.metadata}")

            except Exception as e:
                print(f"   ❌ 测试异常: {e}")
                import traceback

                traceback.print_exc()

            print()

        # 测试通过AI服务的generate_virtual_ip_image方法
        print("🖼️  测试AI服务的generate_virtual_ip_image方法")
        try:
            result = await ai_service.generate_virtual_ip_image(
                ip_name="测试角色",
                description="一个活泼可爱的年轻女孩，充满好奇心和冒险精神",
                style="cartoon",
                category="portrait",
                model="kling-image",
                additional_prompts=["高质量", "精致细节"],
            )

            if result:
                print("   ✅ generate_virtual_ip_image 调用成功!")
                print(f"   生成方法: {result.get('generation_method', 'N/A')}")
                print(f"   提供商: {result.get('provider_used', 'N/A')}")
                print(f"   模型: {result.get('model_used', 'N/A')}")
                print(f"   图像URL: {result.get('image_url', 'N/A')}")
            else:
                print("   ❌ generate_virtual_ip_image 调用失败")

        except Exception as e:
            print(f"   ❌ generate_virtual_ip_image 异常: {e}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """主函数"""
    await test_keling_with_retries()
    print("\n✨ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
