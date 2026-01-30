import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_service import AIService


@pytest.mark.asyncio
async def test_full_image_generation_workflow(skip_if_no_openai):
    """测试完整的图像生成工作流程"""

    # 初始化AI服务
    ai_service = AIService()

    # 测试参数
    ip_name = "小雅"
    description = "一个活泼可爱的年轻女孩，充满好奇心和冒险精神"
    style = "realistic"
    category = "portrait"
    model = "dall-e-3"
    additional_prompts = ["test image generation"]

    print("\n🧪 测试完整图像生成工作流程")
    print(f"   虚拟IP: {ip_name}")
    print(f"   描述: {description}")
    print(f"   风格: {style}")
    print(f"   类别: {category}")
    print(f"   模型: {model}")

    # 调用完整的图像生成方法
    result = await ai_service.generate_virtual_ip_image(
        ip_name=ip_name,
        description=description,
        style=style,
        category=category,
        model=model,
        additional_prompts=additional_prompts,
    )

    print(f"   结果: {result is not None}")
    if result:
        print(f"   返回字段: {list(result.keys())}")
        if "local_file_path" in result:
            local_path = result["local_file_path"]
            print(f"   本地文件: {local_path}")
            print(f"   文件存在: {os.path.exists(local_path) if local_path else False}")
            if local_path and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print(f"   文件大小: {file_size} bytes")

        if "oss_upload" in result:
            oss_result = result["oss_upload"]
            print(f"   OSS上传: {oss_result}")
    else:
        print("   ❌ generate_virtual_ip_image返回None")

    # 断言
    assert result is not None, "generate_virtual_ip_image should return result"
    assert "image_url" in result, "Result should contain image_url"
    assert "local_file_path" in result, "Result should contain local_file_path"
    assert "prompt" in result, "Result should contain prompt"

    # 检查本地文件
    local_path = result["local_file_path"]
    assert local_path is not None, "local_file_path should not be None"
    assert os.path.exists(local_path), f"Local file should exist: {local_path}"
    assert (
        os.path.getsize(local_path) > 1000
    ), "Generated image file should be substantial"
