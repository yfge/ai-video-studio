#!/usr/bin/env python3
"""
调试可灵AI图像生成功能

详细调试可灵AI的集成问题
"""

import asyncio
import os
import sys
import httpx
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_service_manager import AIServiceManager, AIServiceConfig
from app.services.providers.base import ProviderConfig
from app.services.providers.keling_provider import KelingProvider
from app.core.config import settings

async def debug_keling_provider():
    """直接调试可灵提供商"""
    print("🔍 直接测试可灵提供商")
    print("=" * 50)
    
    if not settings.KELING_API_KEY or not settings.KELING_SECRET_KEY:
        print("❌ 缺少可灵AI配置")
        return
    
    try:
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
        print(f"   支持的模型类型: {[mt.value for mt in provider.supported_model_types]}")
        print(f"   可用模型数量: {len(provider.available_models)}")
        
        # 打印可用模型
        print("\n📋 可用模型:")
        for model in provider.available_models:
            print(f"   - {model.model_id}: {model.name}")
            print(f"     类型: {model.model_type.value}")
            print(f"     功能: {model.capabilities}")
        
        # 测试图像生成
        print("\n🎨 测试图像生成...")
        
        test_prompt = "一个可爱的小女孩，卡通风格，高质量"
        
        print(f"提示词: {test_prompt}")
        print("开始调用可灵AI API...")
        
        response = await provider.generate_image(
            prompt=test_prompt,
            model="kling-image",
            width=1024,
            height=1024,
            style="cartoon"
        )
        
        print(f"\n📊 API响应:")
        print(f"   成功: {response.success}")
        print(f"   错误: {response.error}")
        print(f"   提供商: {response.provider}")
        print(f"   模型: {response.model}")
        print(f"   数据: {response.data}")
        print(f"   元数据: {response.metadata}")
        
    except Exception as e:
        print(f"❌ 提供商测试失败: {e}")
        import traceback
        traceback.print_exc()


async def debug_http_request():
    """直接调试HTTP请求"""
    print("\n🌐 直接测试HTTP请求")
    print("=" * 50)
    
    if not settings.KELING_API_KEY:
        print("❌ 缺少API密钥")
        return
    
    try:
        # 测试可灵AI API连通性
        test_urls = [
            "https://klingai.com/api/v1/images/generate",
            "https://api.klingai.com/v1/images/generate",
            "https://app.klingai.com/api/v1/images/generate"
        ]
        
        for url in test_urls:
            print(f"\n🔗 测试URL: {url}")
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {
                        "Authorization": f"Bearer {settings.KELING_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "ai-video-studio/1.0"
                    }
                    
                    # 测试请求数据
                    request_data = {
                        "prompt": "一个简单的测试图片",
                        "width": 512,
                        "height": 512,
                        "model": "kling-image",
                        "num_outputs": 1
                    }
                    
                    print(f"   请求头: {headers}")
                    print(f"   请求数据: {request_data}")
                    
                    response = await client.post(url, json=request_data, headers=headers)
                    
                    print(f"   响应状态: {response.status_code}")
                    print(f"   响应头: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ 成功响应: {data}")
                    else:
                        print(f"   ❌ 错误响应: {response.text[:500]}")
                        
            except Exception as e:
                print(f"   ❌ 请求失败: {e}")
    
    except Exception as e:
        print(f"❌ HTTP调试失败: {e}")


async def debug_ai_manager():
    """调试AI管理器"""
    print("\n🤖 测试AI管理器")
    print("=" * 50)
    
    try:
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        if not ai_service.ai_manager:
            print("❌ AI管理器未初始化")
            return
        
        print("✅ AI管理器初始化成功")
        
        # 获取提供商状态
        status = ai_service.ai_manager.get_provider_status()
        
        print("\n📊 提供商状态:")
        for name, provider_status in status.items():
            print(f"   {name}: {provider_status}")
        
        # 检查可灵提供商
        if "keling" in status:
            keling_status = status["keling"]
            print(f"\n🎯 可灵提供商详情:")
            for key, value in keling_status.items():
                print(f"   {key}: {value}")
        
        # 测试图像生成
        print(f"\n🎨 通过AI管理器测试图像生成...")
        
        response = await ai_service.ai_manager.generate_image(
            prompt="一个测试图片",
            model="kling-image",
            prefer_provider="keling",
            width=512,
            height=512
        )
        
        print(f"   响应: {response}")
        print(f"   成功: {response.success}")
        print(f"   错误: {response.error}")
        print(f"   数据: {response.data}")
        
    except Exception as e:
        print(f"❌ AI管理器调试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("🔧 可灵AI详细调试脚本")
    print("🎯 目标: 找出可灵AI集成问题")
    print("")
    
    # 显示配置状态
    print(f"📋 环境配置:")
    print(f"   KELING_API_KEY: {'✅已配置' if settings.KELING_API_KEY else '❌未配置'}")
    print(f"   KELING_SECRET_KEY: {'✅已配置' if settings.KELING_SECRET_KEY else '❌未配置'}")
    
    if settings.KELING_API_KEY:
        print(f"   API Key前缀: {settings.KELING_API_KEY[:10]}...")
    
    # 依次执行调试步骤
    await debug_keling_provider()
    await debug_http_request() 
    await debug_ai_manager()
    
    print("\n✨ 调试完成!")


if __name__ == "__main__":
    asyncio.run(main())