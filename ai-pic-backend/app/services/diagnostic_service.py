"""
AI图像生成诊断服务

提供完整的自测机制，用于诊断和修复AI图像生成过程中的各种问题
"""

import os
import asyncio
import httpx
import base64
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import get_db
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.services.ai_service import ai_service
from app.services.storage.oss_service import oss_service


class DiagnosticService:
    """AI图像生成诊断服务"""
    
    def __init__(self):
        self.logger = get_logger()
        self.test_results = {}
        self.errors = []
        
    def _log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """记录测试结果"""
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            self.logger.info(f"✅ {test_name}: {details}")
        else:
            self.logger.error(f"❌ {test_name}: {error}")
            self.errors.append(f"{test_name}: {error}")
    
    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """运行完整的诊断测试"""
        self.logger.info("🚀 开始运行完整的AI图像生成诊断测试")
        self.test_results = {}
        self.errors = []
        
        # 1. 环境配置检查
        await self.test_environment_config()
        
        # 2. 数据库连接测试
        await self.test_database_connection()
        
        # 3. OpenAI API测试
        await self.test_openai_api()
        
        # 4. OSS服务测试  
        await self.test_oss_service()
        
        # 5. 文件系统测试
        await self.test_file_system()
        
        # 6. 端到端图像生成测试
        if len(self.errors) == 0:
            await self.test_end_to_end_image_generation()
        else:
            self._log_test_result(
                "端到端测试", 
                False, 
                error="跳过端到端测试，因为前置条件测试失败"
            )
        
        # 7. 生成诊断报告
        report = self.generate_diagnostic_report()
        
        self.logger.info("🏁 诊断测试完成")
        return report
    
    async def test_environment_config(self) -> bool:
        """测试环境配置"""
        self.logger.info("🔍 测试环境配置...")
        
        required_configs = [
            ("OPENAI_API_KEY", "OpenAI API密钥"),
            ("UPLOAD_DIR", "上传目录"),
        ]
        
        optional_configs = [
            ("ALIYUN_ACCESS_KEY_ID", "阿里云访问密钥ID"),
            ("ALIYUN_ACCESS_KEY_SECRET", "阿里云访问密钥"),
            ("ALIYUN_OSS_ENDPOINT", "阿里云OSS端点"),
            ("ALIYUN_OSS_BUCKET", "阿里云OSS存储桶"),
        ]
        
        config_status = {}
        missing_required = []
        
        # 检查必需配置
        for config_name, description in required_configs:
            value = getattr(settings, config_name, None)
            if value:
                config_status[config_name] = f"✅ 已配置 ({description})"
            else:
                config_status[config_name] = f"❌ 未配置 ({description})"
                missing_required.append(config_name)
        
        # 检查可选配置
        for config_name, description in optional_configs:
            value = getattr(settings, config_name, None)
            if value:
                config_status[config_name] = f"✅ 已配置 ({description})"
            else:
                config_status[config_name] = f"⚠️  未配置 ({description}) - 可选"
        
        # 特殊检查：AI服务配置
        if hasattr(ai_service, 'openai_api_key') and ai_service.openai_api_key:
            config_status["AI_SERVICE_OPENAI"] = "✅ AI服务OpenAI配置正常"
        else:
            config_status["AI_SERVICE_OPENAI"] = "❌ AI服务OpenAI配置异常"
            missing_required.append("AI_SERVICE_OPENAI")
        
        success = len(missing_required) == 0
        details = "\n".join([f"  {k}: {v}" for k, v in config_status.items()])
        error = f"缺少必需配置: {', '.join(missing_required)}" if missing_required else ""
        
        self._log_test_result("环境配置检查", success, details, error)
        return success
    
    async def test_database_connection(self) -> bool:
        """测试数据库连接"""
        self.logger.info("🔍 测试数据库连接...")
        
        try:
            db = next(get_db())
            
            # 测试查询虚拟IP
            virtual_ips = db.query(VirtualIP).limit(3).all()
            ip_count = len(virtual_ips)
            
            # 测试查询图像
            images = db.query(VirtualIPImage).limit(5).all()
            image_count = len(images)
            
            db.close()
            
            details = f"虚拟IP数量: {ip_count}, 图像数量: {image_count}"
            self._log_test_result("数据库连接", True, details)
            return True
            
        except Exception as e:
            self._log_test_result("数据库连接", False, error=f"数据库连接失败: {str(e)}")
            return False
    
    async def test_openai_api(self) -> bool:
        """测试OpenAI API连接"""
        self.logger.info("🔍 测试OpenAI API...")
        
        if not hasattr(ai_service, 'openai_api_key') or not ai_service.openai_api_key:
            self._log_test_result("OpenAI API", False, error="OpenAI API密钥未配置")
            return False
        
        try:
            # 测试简单的文本生成请求
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ai_service.openai_api_key}",
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
                    self._log_test_result("OpenAI API", True, details)
                    return True
                else:
                    error_msg = f"API返回错误: {response.status_code} - {response.text[:200]}"
                    self._log_test_result("OpenAI API", False, error=error_msg)
                    return False
                    
        except Exception as e:
            self._log_test_result("OpenAI API", False, error=f"API请求异常: {str(e)}")
            return False
    
    async def test_oss_service(self) -> bool:
        """测试OSS服务"""
        self.logger.info("🔍 测试OSS服务...")
        
        if not oss_service:
            self._log_test_result("OSS服务", False, error="OSS服务未初始化（配置可能不完整）")
            return False
        
        try:
            # 创建测试文件内容
            test_content = b"This is a test file for OSS diagnostic"
            test_filename = "diagnostic_test.txt"
            
            # 测试上传
            upload_result = await oss_service.upload_file_content(
                file_content=test_content,
                filename=test_filename,
                file_type="text",
                prefix="diagnostic-test",
                metadata={"test": "true", "purpose": "diagnostic"}
            )
            
            if upload_result.get("success"):
                file_url = upload_result.get("file_url")
                object_key = upload_result.get("object_key")
                
                # 测试删除（清理）
                try:
                    delete_result = oss_service.delete_object(object_key)
                    cleanup_status = "已清理" if delete_result.get("success") else "清理失败"
                except Exception:
                    cleanup_status = "清理异常"
                
                details = f"上传成功，文件URL: {file_url}, {cleanup_status}"
                self._log_test_result("OSS服务", True, details)
                return True
            else:
                error_msg = upload_result.get("error", "上传失败，原因未知")
                self._log_test_result("OSS服务", False, error=error_msg)
                return False
                
        except Exception as e:
            self._log_test_result("OSS服务", False, error=f"OSS测试异常: {str(e)}")
            return False

    async def test_oss_image_upload(self) -> bool:
        """使用PNG图片测试OSS上传（模拟虚拟IP图像路径）"""
        self.logger.info("🔍 测试OSS图片上传...")

        if not oss_service:
            self._log_test_result("OSS图片上传", False, error="OSS服务未初始化（配置可能不完整）")
            return False

        try:
            import base64

            # 一个最小的 1x1 PNG（白色像素）
            tiny_png_b64 = (
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMA"
                "ASsJTYQAAAAASUVORK5CYII="
            )
            file_content = base64.b64decode(tiny_png_b64)
            filename = "diagnostic_test.png"

            upload_result = await oss_service.upload_file_content(
                file_content=file_content,
                filename=filename,
                file_type="image",
                prefix="diagnostic-test",
                metadata={
                    "test": "true",
                    "purpose": "diagnostic_image",
                    "provider": "diagnostic",
                    "model": "diagnostic-image",
                },
            )

            if upload_result.get("success"):
                file_url = upload_result.get("file_url")
                object_key = upload_result.get("object_key")

                # 测试删除（清理）
                try:
                    delete_result = oss_service.delete_object(object_key)
                    cleanup_status = "已清理" if delete_result.get("success") else "清理失败"
                except Exception:
                    cleanup_status = "清理异常"

                details = f"图片上传成功，文件URL: {file_url}, {cleanup_status}"
                self._log_test_result("OSS图片上传", True, details)
                return True
            else:
                error_msg = upload_result.get("error", "上传失败，原因未知")
                self._log_test_result("OSS图片上传", False, error=error_msg)
                return False

        except Exception as e:
            self._log_test_result("OSS图片上传", False, error=f"OSS图片测试异常: {str(e)}")
            return False
    
    async def test_file_system(self) -> bool:
        """测试文件系统操作"""
        self.logger.info("🔍 测试文件系统...")
        
        try:
            # 检查上传目录
            upload_dir = settings.UPLOAD_DIR
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                creation_status = "已创建"
            else:
                creation_status = "已存在"
            
            # 测试写入权限
            test_file_path = os.path.join(upload_dir, "diagnostic_test.txt")
            test_content = f"Diagnostic test at {datetime.now().isoformat()}"
            
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 测试读取
            with open(test_file_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            # 清理测试文件
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
            
            # 检查权限
            can_read = os.access(upload_dir, os.R_OK)
            can_write = os.access(upload_dir, os.W_OK)
            can_execute = os.access(upload_dir, os.X_OK)
            
            details = f"目录: {upload_dir} ({creation_status}), 权限: R({can_read}) W({can_write}) X({can_execute})"
            success = can_read and can_write and can_execute and read_content == test_content
            
            if success:
                self._log_test_result("文件系统", True, details)
            else:
                self._log_test_result("文件系统", False, error=f"权限或读写测试失败: {details}")
            
            return success
            
        except Exception as e:
            self._log_test_result("文件系统", False, error=f"文件系统测试异常: {str(e)}")
            return False
    
    async def test_end_to_end_image_generation(self) -> bool:
        """测试端到端图像生成"""
        self.logger.info("🔍 测试端到端图像生成...")
        
        try:
            # 获取测试用的虚拟IP
            db = next(get_db())
            test_virtual_ip = db.query(VirtualIP).first()
            
            if not test_virtual_ip:
                db.close()
                self._log_test_result("端到端测试", False, error="没有找到测试用的虚拟IP")
                return False
            
            # 调用AI图像生成服务
            result = await ai_service.generate_virtual_ip_image(
                ip_name=test_virtual_ip.name,
                description=test_virtual_ip.description or "测试用虚拟IP",
                style="realistic",
                category="portrait", 
                model="dall-e-3",
                additional_prompts=["diagnostic test"]
            )
            
            if not result:
                db.close()
                self._log_test_result("端到端测试", False, error="AI图像生成返回None")
                return False
            
            # 检查结果完整性
            local_file_path = result.get("local_file_path")
            image_url = result.get("image_url")
            oss_upload = result.get("oss_upload")
            
            checks = []
            
            # 检查本地文件
            if local_file_path and os.path.exists(local_file_path):
                file_size = os.path.getsize(local_file_path)
                checks.append(f"✅ 本地文件: {local_file_path} ({file_size} bytes)")
            else:
                checks.append("❌ 本地文件不存在")
            
            # 检查OSS上传
            if oss_upload and oss_upload.get("success"):
                checks.append(f"✅ OSS上传: {oss_upload.get('file_url')}")
            else:
                oss_error = oss_upload.get("error") if oss_upload else "OSS结果为空"
                checks.append(f"❌ OSS上传失败: {oss_error}")
            
            # 检查返回的URL
            if image_url:
                checks.append(f"✅ 返回URL: {image_url}")
            else:
                checks.append("❌ 未返回图像URL")
            
            db.close()
            
            # 综合判断
            success = all("✅" in check for check in checks)
            details = "\n".join([f"  {check}" for check in checks])
            
            if success:
                self._log_test_result("端到端测试", True, details)
                
                # 清理测试文件
                if local_file_path and os.path.exists(local_file_path):
                    try:
                        os.remove(local_file_path)
                        self.logger.info(f"已清理测试文件: {local_file_path}")
                    except Exception as e:
                        self.logger.warning(f"清理测试文件失败: {e}")
            else:
                self._log_test_result("端到端测试", False, error=f"部分检查失败:\n{details}")
            
            return success
            
        except Exception as e:
            self._log_test_result("端到端测试", False, error=f"端到端测试异常: {str(e)}")
            return False
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """生成诊断报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "overall_status": "PASS" if failed_tests == 0 else "FAIL",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            "timestamp": datetime.now().isoformat()
        }
        
        recommendations = []
        
        # 基于错误生成建议
        for error in self.errors:
            if "OpenAI API" in error:
                recommendations.append("🔧 检查OPENAI_API_KEY环境变量配置")
                recommendations.append("🔧 验证OpenAI账户余额和API权限")
            elif "OSS" in error:
                recommendations.append("🔧 检查阿里云OSS相关环境变量配置")
                recommendations.append("🔧 验证阿里云账户权限和存储桶设置")
            elif "数据库" in error:
                recommendations.append("🔧 检查数据库连接配置")
                recommendations.append("🔧 确保数据库服务正常运行")
            elif "文件系统" in error:
                recommendations.append("🔧 检查upload目录权限设置")
                recommendations.append("🔧 确保磁盘空间充足")
        
        if failed_tests == 0:
            recommendations.append("🎉 所有测试通过！AI图像生成功能应该正常工作")
        
        return {
            "summary": summary,
            "test_results": self.test_results,
            "errors": self.errors,
            "recommendations": recommendations
        }
    
    async def quick_health_check(self) -> Dict[str, Any]:
        """快速健康检查"""
        self.logger.info("⚡ 运行快速健康检查")
        
        checks = {}
        
        # API密钥检查
        checks["openai_configured"] = bool(getattr(ai_service, 'openai_api_key', None))
        
        # OSS服务检查
        checks["oss_configured"] = oss_service is not None
        
        # 上传目录检查
        upload_dir = settings.UPLOAD_DIR
        checks["upload_dir_exists"] = os.path.exists(upload_dir)
        checks["upload_dir_writable"] = os.access(upload_dir, os.W_OK) if os.path.exists(upload_dir) else False
        
        # 数据库检查
        try:
            db = next(get_db())
            db.query(VirtualIP).first()
            checks["database_accessible"] = True
            db.close()
        except Exception:
            checks["database_accessible"] = False
        
        overall_health = all(checks.values())
        
        return {
            "healthy": overall_health,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }


# 创建全局诊断服务实例
diagnostic_service = DiagnosticService()
