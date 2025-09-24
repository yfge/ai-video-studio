#!/usr/bin/env python3
"""
直接测试可灵AI提供商

绕过AI服务管理器，直接测试可灵AI提供商
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.providers.base import ProviderConfig
from app.services.providers.keling_provider import KelingProvider
from app.core.config import settings

async def test_keling_provider_directly():
    """直接测试可灵AI提供商"""
    print("🔧 直接测试可灵AI提供商")
    print("=" * 50)
    
    if not settings.KELING_API_KEY or not settings.KELING_SECRET_KEY:
        print("❌ 缺少可灵AI配置")
        return
    
    # 创建可灵提供商配置
    config = ProviderConfig(
        name="keling",
        api_key=settings.KELING_API_KEY,
        api_secret=settings.KELING_SECRET_KEY,
        base_url="https://klingai.com/api/v1",
        timeout=120.0
    )
    
    # 创建可灵提供商实例
    provider = KelingProvider(config)
    print(f"✅ 可灵提供商创建成功")
    print(f"   名称: {provider.name}")
    print(f"   基础URL: {provider.base_url}")
    print()
    
    # 测试图像生成（使用修复后的重试机制）
    print("🎨 测试图像生成...")
    test_prompt = "一个可爱的小女孩，卡通风格，高质量"
    print(f"提示词: {test_prompt}")
    print("开始调用可灵AI API（支持重试）...")
    
    try:
        response = await provider.generate_image(
            prompt=test_prompt,
            model="kling-image",
            width=1024,
            height=1024,
            style="cartoon"
        )
        
        print(f"\n📊 API响应:")
        print(f"   成功: {response.success}")
        print(f"   提供商: {response.provider}")
        print(f"   模型: {response.model}")
        
        if response.success:
            print(f"   ✅ 生成成功!")
            print(f"   数据: {response.data}")
            if response.data and 'images' in response.data:
                images = response.data['images']
                print(f"   图像数量: {len(images)}")
                for i, img_url in enumerate(images):
                    print(f"   图像 {i+1}: {img_url}")
        else:
            print(f"   ❌ 生成失败: {response.error}")
        
        print(f"   元数据: {response.metadata}")
        
    except Exception as e:
        print(f"❌ 提供商测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    await test_keling_provider_directly()
    print("\n✨ 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())