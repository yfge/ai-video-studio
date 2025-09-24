import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_service import AIService
from app.core.config import settings

@pytest.mark.asyncio
async def test_openai_dalle_generation(skip_if_no_openai):
    """测试OpenAI DALL-E图像生成方法"""
    
    # 初始化AI服务（就像在完整应用中一样）
    ai_service = AIService()
    
    # 测试参数
    prompt = "A simple test image"
    style = "realistic" 
    category = "portrait"
    
    print(f"\n🧪 测试OpenAI DALL-E图像生成")
    print(f"   提示词: {prompt}")
    print(f"   风格: {style}")
    print(f"   类别: {category}")
    
    # 直接测试AI服务的方法
    result = await ai_service._generate_with_openai_dalle(prompt, style, category)
    
    print(f"   结果类型: {type(result)}")
    if result:
        if result.startswith("data:image/png;base64,"):
            print(f"   格式: base64 (长度: {len(result)})")
        else:
            print(f"   格式: URL ({result[:50]}...)")
    
    # 断言
    assert result is not None, "OpenAI DALL-E should return result"
    assert isinstance(result, str), "Result should be a string"
    
    # 检查是否是base64格式
    if result.startswith("data:image/png;base64,"):
        assert len(result) > 1000, "Base64 image data should be substantial"
    else:
        assert result.startswith("http"), "Should be URL if not base64"