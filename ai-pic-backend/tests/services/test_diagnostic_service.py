"""
诊断服务测试

测试AI图像生成系统的各项诊断功能
"""

import pytest
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.diagnostic_service import DiagnosticService
from app.services.storage.oss_service import oss_service


@pytest.mark.diagnostic
class TestDiagnosticService:
    """诊断服务测试类"""
    
    @pytest.fixture
    def diagnostic_service(self):
        """创建诊断服务实例"""
        return DiagnosticService()
    
    @pytest.mark.asyncio
    async def test_quick_health_check(self, diagnostic_service):
        """测试快速健康检查"""
        result = await diagnostic_service.quick_health_check()
        
        assert "healthy" in result
        assert "checks" in result
        assert "timestamp" in result
        assert isinstance(result["checks"], dict)
        
        # 检查必要的检查项
        expected_checks = [
            "openai_configured",
            "oss_configured", 
            "upload_dir_exists",
            "upload_dir_writable",
            "database_accessible"
        ]
        
        for check in expected_checks:
            assert check in result["checks"]
    
    @pytest.mark.asyncio
    async def test_test_environment_config(self, diagnostic_service):
        """测试环境配置检查"""
        success = await diagnostic_service.test_environment_config()
        
        # 检查测试结果记录
        assert "环境配置检查" in diagnostic_service.test_results
        result = diagnostic_service.test_results["环境配置检查"]
        
        assert "success" in result
        assert "details" in result
        assert "timestamp" in result
        
        # 如果成功，应该没有错误信息
        if result["success"]:
            assert result["error"] == ""
    
    @pytest.mark.asyncio
    @pytest.mark.database
    async def test_test_database_connection(self, diagnostic_service):
        """测试数据库连接测试"""
        success = await diagnostic_service.test_database_connection()
        
        assert "数据库连接" in diagnostic_service.test_results
        result = diagnostic_service.test_results["数据库连接"]
        
        assert isinstance(result["success"], bool)
        
        if result["success"]:
            # 成功的情况下应该有详细信息
            assert "虚拟IP数量" in result["details"]
            assert "图像数量" in result["details"]
    
    @pytest.mark.asyncio
    @pytest.mark.openai
    @pytest.mark.external
    async def test_test_openai_api(self, diagnostic_service, skip_if_no_openai):
        """测试OpenAI API连接"""
        success = await diagnostic_service.test_openai_api()
        
        assert "OpenAI API" in diagnostic_service.test_results
        result = diagnostic_service.test_results["OpenAI API"]
        
        assert isinstance(result["success"], bool)
        
        # 如果有API密钥，应该能够测试成功（假设网络正常）
        if success:
            assert "API正常" in result["details"]
    
    @pytest.mark.asyncio
    @pytest.mark.oss
    @pytest.mark.external 
    async def test_test_oss_service(self, diagnostic_service, skip_if_no_oss):
        """测试OSS服务"""
        success = await diagnostic_service.test_oss_service()
        
        assert "OSS服务" in diagnostic_service.test_results
        result = diagnostic_service.test_results["OSS服务"]
        
        assert isinstance(result["success"], bool)
        
        if success:
            assert "上传成功" in result["details"]
    
    @pytest.mark.asyncio
    async def test_test_file_system(self, diagnostic_service):
        """测试文件系统操作"""
        success = await diagnostic_service.test_file_system()
        
        assert "文件系统" in diagnostic_service.test_results
        result = diagnostic_service.test_results["文件系统"]
        
        assert isinstance(result["success"], bool)
        
        if success:
            assert "权限: R(True) W(True) X(True)" in result["details"]
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.external
    async def test_test_end_to_end_image_generation(self, diagnostic_service, skip_if_no_openai):
        """测试端到端图像生成（需要外部服务）"""
        # 这个测试需要实际的虚拟IP数据，可能需要mock
        with patch('app.services.ai_service.ai_service.generate_virtual_ip_image') as mock_generate:
            # Mock返回成功的图像生成结果
            mock_generate.return_value = {
                "local_file_path": "/tmp/test_image.png",
                "image_url": "https://example.com/image.png",
                "oss_upload": {"success": True, "file_url": "https://oss.example.com/image.png"},
                "prompt": "test prompt",
                "style": "realistic",
                "category": "portrait"
            }
            
            # Mock文件存在
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1024):
                    success = await diagnostic_service.test_end_to_end_image_generation()
                    
                    assert "端到端测试" in diagnostic_service.test_results
                    result = diagnostic_service.test_results["端到端测试"]
                    
                    assert isinstance(result["success"], bool)
    
    @pytest.mark.asyncio
    async def test_full_diagnostic(self, diagnostic_service):
        """测试完整诊断流程"""
        # 使用mock来避免实际的外部服务调用
        with patch.object(diagnostic_service, 'test_openai_api', return_value=True):
            with patch.object(diagnostic_service, 'test_oss_service', return_value=True):
                with patch.object(diagnostic_service, 'test_end_to_end_image_generation', return_value=True):
                    
                    result = await diagnostic_service.run_full_diagnostic()
                    
                    # 检查返回结构
                    assert "summary" in result
                    assert "test_results" in result
                    assert "errors" in result
                    assert "recommendations" in result
                    
                    # 检查summary结构
                    summary = result["summary"]
                    assert "overall_status" in summary
                    assert "total_tests" in summary
                    assert "passed_tests" in summary
                    assert "failed_tests" in summary
                    assert "success_rate" in summary
                    assert "timestamp" in summary
    
    @pytest.mark.asyncio
    async def test_generate_diagnostic_report(self, diagnostic_service):
        """测试诊断报告生成"""
        # 先运行一些测试以生成结果
        await diagnostic_service.test_environment_config()
        await diagnostic_service.test_file_system()
        
        report = diagnostic_service.generate_diagnostic_report()
        
        assert "summary" in report
        assert "test_results" in report
        assert "errors" in report
        assert "recommendations" in report
        
        # 检查summary计算是否正确
        summary = report["summary"]
        total_tests = len(diagnostic_service.test_results)
        assert summary["total_tests"] == total_tests
        
        passed_tests = sum(1 for result in diagnostic_service.test_results.values() if result["success"])
        assert summary["passed_tests"] == passed_tests


@pytest.mark.diagnostic
@pytest.mark.unit
class TestDiagnosticServiceUtils:
    """诊断服务工具函数测试"""
    
    def test_log_test_result(self):
        """测试测试结果记录"""
        diagnostic = DiagnosticService()
        
        # 测试成功结果记录
        diagnostic._log_test_result("测试项目", True, "成功详情", "")
        
        assert "测试项目" in diagnostic.test_results
        result = diagnostic.test_results["测试项目"]
        
        assert result["success"] is True
        assert result["details"] == "成功详情"
        assert result["error"] == ""
        assert "timestamp" in result
        
        # 测试失败结果记录
        diagnostic._log_test_result("失败项目", False, "", "错误信息")
        
        assert "失败项目" in diagnostic.test_results
        result = diagnostic.test_results["失败项目"]
        
        assert result["success"] is False
        assert result["details"] == ""
        assert result["error"] == "错误信息"
        
        # 错误应该被添加到errors列表
        assert "失败项目: 错误信息" in diagnostic.errors