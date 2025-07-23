#!/usr/bin/env python3
"""
AI图像生成功能测试脚本
用于测试虚拟IP图像生成功能是否正常工作
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai_service import ai_service
from app.core.config import settings

async def test_ai_generation():
    """测试AI图像生成功能"""
    print("🤖 AI图像生成功能测试")
    print("=" * 50)
    
    # 检查配置
    print("📋 检查AI服务配置...")
    if not settings.OPENAI_API_KEY and not settings.STABILITY_API_KEY and not settings.AI_API_KEY:
        print("❌ 未配置任何AI服务API Key")
        print("请配置以下环境变量之一：")
        print("  - OPENAI_API_KEY (推荐)")
        print("  - STABILITY_API_KEY")
        print("  - AI_SERVICE_URL + AI_API_KEY")
        return False
    
    if settings.OPENAI_API_KEY:
        print("✅ OpenAI API Key 已配置")
    if settings.STABILITY_API_KEY:
        print("✅ Stability AI API Key 已配置")
    if settings.AI_SERVICE_URL and settings.AI_API_KEY:
        print("✅ 自定义AI服务已配置")
    
    # 测试图像生成
    print("\n🎨 测试图像生成...")
    
    test_cases = [
        {
            "name": "写实风格肖像",
            "style": "realistic",
            "category": "portrait",
            "additional_prompts": "smiling, professional lighting"
        },
        {
            "name": "动漫风格全身像",
            "style": "anime",
            "category": "full_body",
            "additional_prompts": "vibrant colors, dynamic pose"
        },
        {
            "name": "卡通风格表情",
            "style": "cartoon",
            "category": "emotion",
            "additional_prompts": "happy, bright background"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📸 测试 {i}: {test_case['name']}")
        print(f"   风格: {test_case['style']}")
        print(f"   类别: {test_case['category']}")
        print(f"   额外提示: {test_case['additional_prompts']}")
        
        try:
            result = await ai_service.generate_virtual_ip_image(
                ip_name="测试虚拟IP",
                description="这是一个用于测试的虚拟IP角色",
                style=test_case['style'],
                category=test_case['category'],
                additional_prompts=[test_case['additional_prompts']]
            )
            
            if result:
                print(f"   ✅ 生成成功!")
                print(f"   图像路径: {result['image_url']}")
                print(f"   生成方法: {result['generation_method']}")
                print(f"   使用提示词: {result['prompt'][:100]}...")
            else:
                print(f"   ❌ 生成失败")
                
        except Exception as e:
            print(f"   ❌ 生成出错: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")
    return True

async def test_prompt_optimization():
    """测试提示词优化功能"""
    print("\n🔧 测试提示词优化...")
    
    test_ip = {
        "name": "魔法少女小樱",
        "description": "一位拥有强大魔法能力的少女，性格活泼开朗，喜欢收集魔法卡牌"
    }
    
    styles = ["realistic", "anime", "cartoon"]
    categories = ["portrait", "full_body", "scene"]
    
    for style in styles:
        for category in categories:
            print(f"\n📝 测试 {style} + {category} 提示词优化:")
            
            result = await ai_service.generate_virtual_ip_image(
                ip_name=test_ip["name"],
                description=test_ip["description"],
                style=style,
                category=category,
                additional_prompts=["magical", "cute"]
            )
            
            if result:
                print(f"   优化后提示词: {result['prompt']}")
            else:
                print(f"   ❌ 提示词优化失败")

def main():
    """主函数"""
    print("🚀 启动AI图像生成测试...")
    
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # 运行测试
    asyncio.run(test_ai_generation())
    asyncio.run(test_prompt_optimization())

if __name__ == "__main__":
    main() 