#!/usr/bin/env python3
"""
简单的OSS连接测试
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import oss2
from datetime import datetime
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

def test_oss_connection():
    """测试OSS基础连接"""
    print("🔍 测试OSS连接...")
    
    # 加载配置
    settings = TestSettings()
    print(f"Access Key ID: {settings.ALIYUN_ACCESS_KEY_ID}")
    print(f"Endpoint: {settings.ALIYUN_OSS_ENDPOINT}")
    print(f"Bucket: {settings.ALIYUN_OSS_BUCKET}")
    
    if not all([settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET, 
                settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET]):
        print("❌ OSS配置不完整")
        return False
    
    try:
        # 创建OSS认证和bucket对象
        auth = oss2.Auth(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET)
        
        # 测试1: 列出bucket中的文件（只取前5个）
        print("\n🔍 测试列出文件...")
        result = bucket.list_objects(max_keys=5)
        print(f"✅ 成功连接，找到 {len(result.object_list)} 个对象")
        
        # 测试2: 上传一个简单的文本文件
        print("\n🔍 测试上传文件...")
        test_content = f"OSS测试文件 - {datetime.now().isoformat()}"
        test_key = f"test/oss_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        bucket.put_object(test_key, test_content)
        print(f"✅ 成功上传测试文件: {test_key}")
        
        # 测试3: 下载文件验证
        print("\n🔍 测试下载文件...")
        downloaded = bucket.get_object(test_key)
        content = downloaded.read().decode('utf-8')
        print(f"✅ 成功下载，内容匹配: {content == test_content}")
        
        # 清理测试文件
        bucket.delete_object(test_key)
        print(f"✅ 已清理测试文件")
        
        return True
        
    except Exception as e:
        print(f"❌ OSS连接失败: {str(e)}")
        return False

def test_oss_with_metadata():
    """测试带metadata的上传"""
    print("\n🔍 测试带metadata的上传...")
    
    settings = TestSettings()
    
    try:
        auth = oss2.Auth(settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, settings.ALIYUN_OSS_ENDPOINT, settings.ALIYUN_OSS_BUCKET)
        
        # 测试不带metadata的上传
        test_content = "测试不带metadata"
        test_key = f"test/no_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        bucket.put_object(test_key, test_content)
        print(f"✅ 无metadata上传成功: {test_key}")
        bucket.delete_object(test_key)
        
        # 测试带ASCII metadata的上传
        test_content = "测试ASCII metadata"
        test_key = f"test/ascii_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        headers = {
            'x-oss-meta-category': 'portrait',
            'x-oss-meta-style': 'realistic',
            'x-oss-meta-provider': 'openai'
        }
        bucket.put_object(test_key, test_content, headers=headers)
        print(f"✅ ASCII metadata上传成功: {test_key}")
        bucket.delete_object(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ metadata测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🕒 当前时间: {datetime.now()}")
    
    if test_oss_connection():
        test_oss_with_metadata()
    else:
        print("\n💡 可能的解决方案:")
        print("1. 检查OSS Access Key和Secret Key是否正确")
        print("2. 检查endpoint配置是否正确")
        print("3. 检查bucket名称是否正确")
        print("4. 检查网络连接")
        print("5. 检查系统时间是否正确（重要！）")