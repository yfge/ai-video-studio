#!/usr/bin/env python3
"""
简化版AI图像生成诊断脚本

不依赖完整的FastAPI应用，直接测试核心功能
"""

import os
import asyncio
import httpx
import base64
import json
from datetime import datetime
from pathlib import Path

# 使用与FastAPI相同的配置加载机制
try:
    from pydantic_settings import BaseSettings
    
    class DiagnosticSettings(BaseSettings):
        OPENAI_API_KEY: str = None
        UPLOAD_DIR: str = "./uploads"
        ALIYUN_ACCESS_KEY_ID: str = None
        ALIYUN_ACCESS_KEY_SECRET: str = None  
        ALIYUN_OSS_ENDPOINT: str = None
        ALIYUN_OSS_BUCKET: str = None
        
        class Config:
            env_file = ".env"
            case_sensitive = True
            extra = "ignore"  # 忽略额外的环境变量
    
    config = DiagnosticSettings()
    print("✅ 已使用FastAPI配置机制加载.env文件")
    
except ImportError:
    print("⚠️  pydantic_settings未安装，使用环境变量")
    print("   安装命令: pip install pydantic-settings")
    config = None


class SimpleDiagnostic:
    """简化诊断工具"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        
        if config:
            # 使用pydantic配置
            self.openai_api_key = config.OPENAI_API_KEY
            self.upload_dir = config.UPLOAD_DIR
            self.oss_access_key = config.ALIYUN_ACCESS_KEY_ID
            self.oss_secret_key = config.ALIYUN_ACCESS_KEY_SECRET
            self.oss_endpoint = config.ALIYUN_OSS_ENDPOINT
            self.oss_bucket = config.ALIYUN_OSS_BUCKET
        else:
            # 回退到环境变量
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            self.upload_dir = os.getenv('UPLOAD_DIR', './uploads')
            self.oss_access_key = os.getenv('ALIYUN_ACCESS_KEY_ID')
            self.oss_secret_key = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
            self.oss_endpoint = os.getenv('ALIYUN_OSS_ENDPOINT')
            self.oss_bucket = os.getenv('ALIYUN_OSS_BUCKET')
    
    def log_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """记录测试结果"""
        self.results[test_name] = {
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"    详情: {details}")
        if error:
            print(f"    错误: {error}")
            self.errors.append(f"{test_name}: {error}")
    
    async def test_environment_config(self):
        """测试环境配置"""
        print("\n🔍 检查环境配置...")
        
        configs = {
            "OPENAI_API_KEY": self.openai_api_key,
            "UPLOAD_DIR": self.upload_dir,
            "ALIYUN_ACCESS_KEY_ID": self.oss_access_key,
            "ALIYUN_ACCESS_KEY_SECRET": self.oss_secret_key,
            "ALIYUN_OSS_ENDPOINT": self.oss_endpoint,
            "ALIYUN_OSS_BUCKET": self.oss_bucket,
        }
        
        configured = []
        missing = []
        
        for name, value in configs.items():
            if value:
                configured.append(name)
            else:
                missing.append(name)
        
        details = f"已配置: {len(configured)}, 缺失: {len(missing)}"
        if missing:
            details += f" (缺失: {', '.join(missing)})"
        
        success = self.openai_api_key is not None  # 至少需要OpenAI配置
        error = "缺少OPENAI_API_KEY" if not success else ""
        
        self.log_result("环境配置检查", success, details, error)
        return success
    
    async def test_openai_api(self):
        """测试OpenAI API"""
        print("\n🔍 测试OpenAI API...")
        
        if not self.openai_api_key:
            self.log_result("OpenAI API", False, error="API密钥未配置")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": "Hello"}],
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    usage = result.get("usage", {})
                    details = f"API正常，使用tokens: {usage.get('total_tokens', 'unknown')}"
                    self.log_result("OpenAI API", True, details)
                    return True
                else:
                    error = f"API返回错误: {response.status_code} - {response.text[:200]}"
                    self.log_result("OpenAI API", False, error=error)
                    return False
                    
        except Exception as e:
            self.log_result("OpenAI API", False, error=f"连接异常: {str(e)}")
            return False
    
    async def test_file_system(self):
        """测试文件系统"""
        print("\n🔍 测试文件系统...")
        
        try:
            # 创建上传目录
            os.makedirs(self.upload_dir, exist_ok=True)
            
            # 测试写入权限
            test_file = os.path.join(self.upload_dir, "test.txt")
            test_content = f"Test at {datetime.now().isoformat()}"
            
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # 测试读取
            with open(test_file, 'r') as f:
                read_content = f.read()
            
            # 清理
            if os.path.exists(test_file):
                os.remove(test_file)
            
            success = read_content == test_content
            details = f"目录: {self.upload_dir}, 读写测试: {'通过' if success else '失败'}"
            
            self.log_result("文件系统", success, details)
            return success
            
        except Exception as e:
            self.log_result("文件系统", False, error=str(e))
            return False
    
    async def test_image_generation(self):
        """测试图像生成"""
        print("\n🔍 测试图像生成...")
        
        if not self.openai_api_key:
            self.log_result("图像生成", False, error="需要OpenAI API密钥")
            return False
        
        try:
            prompt = "A simple test image"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "quality": "hd",
                        "style": "natural",
                        "response_format": "b64_json"
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "b64_json" in result["data"][0]:
                        base64_data = result["data"][0]["b64_json"]
                        
                        # 保存图像
                        import uuid
                        filename = f"test_{uuid.uuid4().hex}.png"
                        file_path = os.path.join(self.upload_dir, filename)
                        
                        image_bytes = base64.b64decode(base64_data)
                        
                        with open(file_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        file_size = os.path.getsize(file_path)
                        details = f"图像生成成功，文件: {filename}, 大小: {file_size} bytes"
                        
                        # 清理测试文件
                        try:
                            os.remove(file_path)
                        except:
                            pass
                        
                        self.log_result("图像生成", True, details)
                        return True
                    else:
                        self.log_result("图像生成", False, error="未收到base64数据")
                        return False
                else:
                    error = f"API返回错误: {response.status_code} - {response.text[:200]}"
                    self.log_result("图像生成", False, error=error)
                    return False
                    
        except Exception as e:
            self.log_result("图像生成", False, error=str(e))
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始AI图像生成诊断测试")
        print("=" * 50)
        
        tests = [
            ("环境配置", self.test_environment_config()),
            ("文件系统", self.test_file_system()),
            ("OpenAI API", self.test_openai_api()),
            ("图像生成", self.test_image_generation()),
        ]
        
        for test_name, test_coro in tests:
            try:
                await test_coro
            except Exception as e:
                self.log_result(test_name, False, error=f"测试异常: {str(e)}")
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 诊断结果总结")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"总体状态: {'✅ PASS' if failed_tests == 0 else '❌ FAIL'}")
        print(f"测试总数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ 发现的问题:")
            for error in self.errors:
                print(f"  • {error}")
            
            print(f"\n🔧 修复建议:")
            if any("OPENAI_API_KEY" in error for error in self.errors):
                print("  • 配置OPENAI_API_KEY环境变量")
                print("  • 验证OpenAI账户余额和API权限")
            
            if any("文件系统" in error for error in self.errors):
                print("  • 检查uploads目录权限")
                print("  • 确保磁盘空间充足")
        else:
            print(f"\n🎉 所有测试通过！AI图像生成功能应该正常工作")
        
        # 保存报告
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results,
            "errors": self.errors
        }
        
        with open("simple_diagnostic_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细报告已保存到: simple_diagnostic_report.json")
        
        return failed_tests == 0


async def main():
    """主函数"""
    diagnostic = SimpleDiagnostic()
    success = await diagnostic.run_all_tests()
    
    if success:
        print(f"\n🎉 所有测试通过！")
        exit(0)
    else:
        print(f"\n❌ 部分测试失败，请查看上述报告")
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        exit(130)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        exit(1)
