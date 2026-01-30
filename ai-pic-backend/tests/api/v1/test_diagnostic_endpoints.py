"""
诊断API端点测试

测试诊断相关的API端点功能
"""

from unittest.mock import patch

import pytest


@pytest.mark.api
@pytest.mark.diagnostic
class TestDiagnosticEndpoints:
    """诊断API端点测试类"""

    def test_health_check_endpoint(self, client):
        """测试快速健康检查端点"""
        response = client.get("/api/v1/diagnostic/health")

        assert response.status_code == 200
        data = response.json()

        assert "healthy" in data
        assert "checks" in data
        assert "timestamp" in data

    def test_openai_test_endpoint_requires_auth(self, client):
        """测试OpenAI测试端点需要认证"""
        response = client.post("/api/v1/diagnostic/openai")

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_openai_test_endpoint_with_auth(self, client, auth_headers):
        """测试带认证的OpenAI测试端点"""
        with patch(
            "app.services.diagnostic_service.diagnostic_service.test_openai_api"
        ) as mock_test:
            mock_test.return_value = True
            mock_result = {
                "success": True,
                "details": "API正常，使用tokens: 10",
                "error": "",
                "timestamp": "2023-01-01T00:00:00",
            }

            # Mock test_results属性
            with patch.object(
                type(mock_test.return_value),
                "test_results",
                new={"OpenAI API": mock_result},
            ):
                response = client.post(
                    "/api/v1/diagnostic/openai", headers=auth_headers
                )

        if auth_headers:  # 只有在有有效认证头时才测试
            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "test_result" in data

    def test_oss_test_endpoint_with_auth(self, client, auth_headers):
        """测试OSS服务测试端点"""
        with patch(
            "app.services.diagnostic_service.diagnostic_service.test_oss_service"
        ) as mock_test:
            mock_test.return_value = True

            response = client.post("/api/v1/diagnostic/oss", headers=auth_headers)

        if auth_headers:
            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "test_result" in data

    def test_database_test_endpoint_with_auth(self, client, auth_headers):
        """测试数据库连接测试端点"""
        response = client.post("/api/v1/diagnostic/database", headers=auth_headers)

        if auth_headers:
            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "test_result" in data

    def test_filesystem_test_endpoint_with_auth(self, client, auth_headers):
        """测试文件系统测试端点"""
        response = client.post("/api/v1/diagnostic/filesystem", headers=auth_headers)

        if auth_headers:
            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "test_result" in data

    def test_end_to_end_test_endpoint_with_auth(self, client, auth_headers):
        """测试端到端测试端点"""
        with patch(
            "app.services.diagnostic_service.diagnostic_service.test_end_to_end_image_generation"
        ) as mock_test:
            mock_test.return_value = True

            response = client.post(
                "/api/v1/diagnostic/end-to-end", headers=auth_headers
            )

        if auth_headers:
            assert response.status_code == 200
            data = response.json()

            assert "success" in data
            assert "test_result" in data

    def test_full_diagnostic_endpoint_with_auth(self, client, auth_headers):
        """测试完整诊断端点"""
        with patch(
            "app.services.diagnostic_service.diagnostic_service.run_full_diagnostic"
        ) as mock_diagnostic:
            mock_diagnostic.return_value = {
                "summary": {
                    "overall_status": "PASS",
                    "total_tests": 5,
                    "passed_tests": 5,
                    "failed_tests": 0,
                    "success_rate": "100.0%",
                    "timestamp": "2023-01-01T00:00:00",
                },
                "test_results": {},
                "errors": [],
                "recommendations": ["🎉 所有测试通过！AI图像生成功能应该正常工作"],
            }

            response = client.post("/api/v1/diagnostic/full", headers=auth_headers)

        if auth_headers:
            assert response.status_code == 200
            data = response.json()

            assert "summary" in data
            assert "test_results" in data
            assert "errors" in data
            assert "recommendations" in data


@pytest.mark.api
@pytest.mark.diagnostic
@pytest.mark.integration
class TestDiagnosticEndpointsIntegration:
    """诊断API端点集成测试"""

    @pytest.mark.asyncio
    async def test_health_check_endpoint_real(self, client):
        """测试真实的健康检查端点"""
        response = client.get("/api/v1/diagnostic/health")

        assert response.status_code == 200
        data = response.json()

        # 验证返回数据结构
        assert isinstance(data["healthy"], bool)
        assert isinstance(data["checks"], dict)

        # 验证必要的检查项
        expected_checks = [
            "openai_configured",
            "oss_configured",
            "upload_dir_exists",
            "upload_dir_writable",
            "database_accessible",
        ]

        for check in expected_checks:
            assert check in data["checks"]
            assert isinstance(data["checks"][check], bool)

    def test_error_handling(self, client, auth_headers):
        """测试错误处理"""
        with patch(
            "app.services.diagnostic_service.diagnostic_service.test_openai_api"
        ) as mock_test:
            # Mock抛出异常
            mock_test.side_effect = Exception("测试异常")

            response = client.post("/api/v1/diagnostic/openai", headers=auth_headers)

        if auth_headers:
            assert response.status_code == 200  # 应该返回200但success为False
            data = response.json()

            assert data["success"] is False
            assert "error" in data
            assert "测试异常" in data["error"]
