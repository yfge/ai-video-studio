#!/usr/bin/env python3
"""
AI图像生成功能演示脚本
展示如何使用AI服务为虚拟IP生成图像
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai_service import ai_service


async def demo_virtual_ip_generation():
    """演示虚拟IP图像生成"""
    print("🎭 虚拟IP AI图像生成演示")
    print("=" * 60)

    # 示例虚拟IP
    virtual_ips = [
        {
            "name": "魔法少女小樱",
            "description": "一位拥有强大魔法能力的少女，性格活泼开朗，喜欢收集魔法卡牌，拥有粉色的长发和可爱的服装",
            "style": "anime",
            "category": "portrait",
            "additional_prompts": ["magical", "cute", "pink hair", "school uniform"],
        },
        {
            "name": "未来战士阿诺",
            "description": "来自未来的机械战士，拥有强大的战斗能力和冷酷的外表，穿着高科技装甲",
            "style": "realistic",
            "category": "full_body",
            "additional_prompts": ["cyborg", "armor", "futuristic", "serious"],
        },
        {
            "name": "可爱小熊波比",
            "description": "一只毛茸茸的小熊，性格温和友善，喜欢蜂蜜和冒险，适合儿童内容",
            "style": "cartoon",
            "category": "emotion",
            "additional_prompts": ["cute", "friendly", "honey", "adventure"],
        },
    ]

    for i, ip in enumerate(virtual_ips, 1):
        print(f"\n🎨 演示 {i}: {ip['name']}")
        print(f"   描述: {ip['description']}")
        print(f"   风格: {ip['style']}")
        print(f"   类别: {ip['category']}")
        print(f"   额外提示: {', '.join(ip['additional_prompts'])}")

        try:
            print("   🔄 正在生成图像...")
            result = await ai_service.generate_virtual_ip_image(
                ip_name=ip["name"],
                description=ip["description"],
                style=ip["style"],
                category=ip["category"],
                additional_prompts=ip["additional_prompts"],
            )

            if result:
                print("   ✅ 生成成功!")
                print(f"   图像路径: {result['image_url']}")
                print(f"   生成方法: {result['generation_method']}")
                print(f"   优化提示词: {result['prompt'][:120]}...")
            else:
                print("   ❌ 生成失败")

        except Exception as e:
            print(f"   ❌ 生成出错: {e}")

        print("-" * 40)


async def demo_style_variations():
    """演示不同风格的图像生成"""
    print("\n🎨 风格变化演示")
    print("=" * 60)

    test_ip = {
        "name": "神秘女巫",
        "description": "一位拥有强大魔法的女巫，穿着长袍，手持魔法杖",
    }

    styles = ["realistic", "anime", "cartoon"]
    categories = ["portrait", "full_body"]

    for style in styles:
        for category in categories:
            print(f"\n🔮 生成 {style} 风格的 {category}")

            try:
                result = await ai_service.generate_virtual_ip_image(
                    ip_name=test_ip["name"],
                    description=test_ip["description"],
                    style=style,
                    category=category,
                    additional_prompts=["mystical", "magical staff", "robes"],
                )

                if result:
                    print(f"   ✅ 成功生成 {style} 风格图像")
                    print(f"   路径: {result['image_url']}")
                else:
                    print("   ❌ 生成失败")

            except Exception as e:
                print(f"   ❌ 生成出错: {e}")


async def demo_prompt_optimization():
    """演示提示词优化功能"""
    print("\n🔧 提示词优化演示")
    print("=" * 60)

    test_cases = [
        {
            "name": "简单描述",
            "description": "一个女孩",
            "expected": "应该自动添加风格和质量提升词",
        },
        {
            "name": "详细描述",
            "description": "一位穿着红色连衣裙的美丽女孩，在花园里微笑",
            "expected": "应该保持原有描述并添加风格词",
        },
        {
            "name": "专业描述",
            "description": "专业摄影师拍摄的模特肖像，使用自然光，背景虚化",
            "expected": "应该优化为AI生成友好的提示词",
        },
    ]

    for case in test_cases:
        print(f"\n📝 测试: {case['name']}")
        print(f"   原始描述: {case['description']}")
        print(f"   期望效果: {case['expected']}")

        try:
            result = await ai_service.generate_virtual_ip_image(
                ip_name="测试角色",
                description=case["description"],
                style="realistic",
                category="portrait",
                additional_prompts=[],
            )

            if result:
                print("   ✅ 优化后提示词:")
                print(f"   {result['prompt']}")
            else:
                print("   ❌ 优化失败")

        except Exception as e:
            print(f"   ❌ 优化出错: {e}")


def main():
    """主函数"""
    print("🚀 AI图像生成功能演示")
    print("请确保已配置AI服务API Key")
    print("=" * 60)

    # 检查配置
    if not any(
        [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("STABILITY_API_KEY"),
            os.getenv("AI_API_KEY"),
        ]
    ):
        print("⚠️  警告: 未检测到AI服务API Key配置")
        print("请配置以下环境变量之一：")
        print("  - OPENAI_API_KEY")
        print("  - STABILITY_API_KEY")
        print("  - AI_SERVICE_URL + AI_API_KEY")
        print("\n演示将继续，但可能无法成功生成图像")

    # 确保上传目录存在
    os.makedirs("uploads", exist_ok=True)

    # 运行演示
    asyncio.run(demo_virtual_ip_generation())
    asyncio.run(demo_style_variations())
    asyncio.run(demo_prompt_optimization())

    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("\n💡 提示:")
    print("- 生成的图像保存在 uploads/ 目录")
    print("- 可以查看生成的提示词了解优化效果")
    print("- 不同AI服务可能有不同的生成效果")
    print("- 建议尝试不同的风格和类别组合")


if __name__ == "__main__":
    main()
