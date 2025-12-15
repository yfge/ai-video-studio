#!/usr/bin/env python3
"""
OpenAI图像生成单元测试 - 独立版本

直接测试OpenAI API调用，不依赖完整的FastAPI应用
"""

import asyncio
import os

import httpx
import pytest
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    OPENAI_API_KEY: str = None

    class Config:
        env_file = ".env"
        case_sensitive = True


if os.getenv("RUN_OPENAI_DIRECT_TEST") != "1":
    pytest.skip(
        "OpenAI 直连 API 冒烟测试（默认跳过）；设置 RUN_OPENAI_DIRECT_TEST=1 才运行",
        allow_module_level=True,
    )


@pytest.mark.openai
@pytest.mark.external
@pytest.mark.asyncio
async def test_openai_dalle_direct(skip_if_no_openai):
    """直接测试OpenAI DALL-E API调用"""

    print("🧪 开始OpenAI DALL-E单元测试（直接API调用）")
    print("=" * 60)

    # 加载配置
    settings = TestSettings()

    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY 未配置")

    # 测试参数
    prompt = "A simple test image of a cat"
    style = "realistic"

    print("🔍 测试参数:")
    print(f"   提示词: {prompt}")
    print(f"   风格: {style}")
    print(f"   API密钥: sk-...{settings.OPENAI_API_KEY[-10:]}")

    try:
        print("\n⏳ 直接调用OpenAI API...")
        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt[:1000],
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "hd",
                    "style": "vivid" if style != "realistic" else "natural",
                    "response_format": "b64_json",
                },
                timeout=60.0,
            )

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            print(f"⏱️ API调用耗时: {duration:.2f}秒")
            print(f"📡 HTTP状态码: {response.status_code}")

            if response.status_code != 200:
                print("❌ API返回错误")
                print(f"   错误内容: {response.text[:300]}")
                return False

            response.raise_for_status()
            result = response.json()

            print("✅ API调用成功")
            print(f"   响应数据结构: {list(result.keys())}")

            if "data" in result and len(result["data"]) > 0:
                data = result["data"][0]
                print(f"   图像数据字段: {list(data.keys())}")

                if "b64_json" in data:
                    base64_data = data["b64_json"]
                    print(f"   base64数据长度: {len(base64_data)}")

                    # 验证base64数据
                    import base64

                    png_header = b"\x89PNG"
                    try:
                        decoded = base64.b64decode(base64_data)
                        print(f"   解码后图像大小: {len(decoded)} bytes")
                        print(
                            f"   图像格式检查: {'PNG' if decoded.startswith(png_header) else '未知'}"
                        )
                        assert decoded.startswith(png_header)
                        return
                    except Exception as decode_error:
                        print(f"   ❌ base64解码失败: {decode_error}")
                        raise
                else:
                    print("   ❌ 响应中没有b64_json字段")
                    raise AssertionError("missing b64_json")
            else:
                print("   ❌ 响应中没有data字段")
                raise AssertionError("missing data")

    except httpx.TimeoutException as e:
        print(f"❌ 请求超时: {e}")
        raise
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP错误: {e.response.status_code}")
        print(f"   错误详情: {e.response.text[:300]}")
        raise
    except Exception as e:
        print(f"❌ 调用异常: {e}")
        print(f"   异常类型: {type(e).__name__}")
        raise


async def main():
    """主测试函数"""
    success = await test_openai_dalle_direct()

    print("\n" + "=" * 60)
    print(f"🎯 单元测试结果: {'✅ 通过' if success else '❌ 失败'}")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        exit(130)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        exit(1)
