#!/usr/bin/env python3
"""
详细的OSS测试，模拟我们代码的确切调用方式
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from datetime import datetime

import oss2
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    ALIYUN_ACCESS_KEY_ID: str = None
    ALIYUN_ACCESS_KEY_SECRET: str = None
    ALIYUN_OSS_ENDPOINT: str = None
    ALIYUN_OSS_BUCKET: str = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


async def test_exact_oss_call():
    """测试与我们代码完全相同的OSS调用"""
    print("🔍 测试与代码完全相同的OSS调用...")

    settings = TestSettings()

    try:
        # 创建OSS连接（与我们代码相同）
        auth = oss2.Auth(
            settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET
        )
        bucket = oss2.Bucket(
            auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET
        )

        # 模拟我们的文件内容
        test_content = b"fake image content for testing"

        # 生成对象键（模拟我们的生成方式）
        timestamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        import uuid

        random_str = str(uuid.uuid4())[:8]
        object_key = f"ai-generated/virtual-ip/image/{timestamp}/{random_str}.png"

        print(f"Object key: {object_key}")

        # 准备headers（与我们代码完全相同）
        headers = {"Content-Type": "image/png", "Cache-Control": "max-age=31536000"}

        # 添加metadata（与我们代码相同）
        metadata = {
            "ip_name": "小雅",  # 这个包含中文，会被跳过
            "style": "realistic",
            "category": "portrait",
            "provider": "openai",
            "model": "dall-e-3",
            "generation_time": datetime.now().isoformat(),
        }

        print(f"原始metadata: {metadata}")

        # 处理metadata（与我们代码相同的逻辑）
        processed_metadata = {}
        for key, value in metadata.items():
            value_str = str(value)
            try:
                value_str.encode("ascii")
                headers[f"x-oss-meta-{key}"] = value_str
                processed_metadata[key] = value_str
            except UnicodeEncodeError:
                print(f"跳过包含非ASCII字符的metadata: {key}={value_str}")
                continue

        print(f"处理后的metadata: {processed_metadata}")
        print(f"最终headers: {headers}")

        # 使用asyncio executor调用（与我们代码相同）
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: bucket.put_object(object_key, test_content, headers=headers)
        )

        print(f"✅ 成功上传: {object_key}")

        # 清理
        bucket.delete_object(object_key)
        print("✅ 已清理测试文件")

        return True

    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")

        # 如果是oss2异常，打印更多详细信息
        if hasattr(e, "details"):
            print(f"错误详情: {e.details}")

        return False


async def test_without_content_type():
    """测试不设置Content-Type的情况"""
    print("\n🔍 测试不设置Content-Type...")

    settings = TestSettings()

    try:
        auth = oss2.Auth(
            settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET
        )
        bucket = oss2.Bucket(
            auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET
        )

        test_content = b"fake image content for testing"

        timestamp = datetime.now().strftime("%Y%m%d/%H%M%S")
        import uuid

        random_str = str(uuid.uuid4())[:8]
        object_key = f"ai-generated/test2/image/{timestamp}/{random_str}.png"

        # 只设置metadata，不设置Content-Type
        headers = {
            "x-oss-meta-category": "portrait",
            "x-oss-meta-style": "realistic",
            "x-oss-meta-provider": "openai",
            "x-oss-meta-model": "dall-e-3",
        }

        print(f"Headers: {headers}")

        await asyncio.get_event_loop().run_in_executor(
            None, lambda: bucket.put_object(object_key, test_content, headers=headers)
        )

        print(f"✅ 成功上传（无Content-Type）: {object_key}")

        bucket.delete_object(object_key)
        print("✅ 已清理测试文件")

        return True

    except Exception as e:
        print(f"❌ 上传失败（无Content-Type）: {str(e)}")
        return False


async def main():
    print(f"🕒 当前时间: {datetime.now()}")

    # 测试1: 完全模拟我们的代码
    success1 = await test_exact_oss_call()

    # 测试2: 不设置Content-Type
    success2 = await test_without_content_type()

    if success1 and success2:
        print("\n✅ 所有测试通过，OSS服务正常")
    else:
        print("\n❌ 存在问题，需要进一步调试")


if __name__ == "__main__":
    asyncio.run(main())
