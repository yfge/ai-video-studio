"""
Tests for domain exception middleware.
"""

import pytest
from app.core.exceptions import (
    DomainError,
    ExternalServiceError,
    GenerationFailedError,
    NotFoundError,
    ValidationError,
)
from app.core.middleware import domain_exception_handler
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_middleware():
    """Create test FastAPI app with domain exception handler."""
    app = FastAPI()
    app.add_exception_handler(DomainError, domain_exception_handler)

    # Test endpoints that raise various exceptions
    @app.get("/test/not-found")
    async def test_not_found():
        raise NotFoundError.user(123)

    @app.get("/test/validation-error")
    async def test_validation_error():
        raise ValidationError("虚拟IP名称已存在")

    @app.get("/test/generation-failed")
    async def test_generation_failed():
        raise GenerationFailedError.image("API超时")

    @app.get("/test/external-service")
    async def test_external_service():
        raise ExternalServiceError("OpenAI", "连接超时")

    @app.get("/test/domain-error-with-context")
    async def test_domain_error_with_context():
        raise NotFoundError("脚本", 456, context={"user_id": 123, "attempt": 3})

    @app.get("/test/success")
    async def test_success():
        return {"message": "success"}

    return app


@pytest.fixture
def client(app_with_middleware):
    """Create test client."""
    return TestClient(app_with_middleware)


class TestDomainExceptionMiddleware:
    """Test domain exception middleware."""

    def test_not_found_error_conversion(self, client):
        """Test that NotFoundError is converted to 404 response."""
        response = client.get("/test/not-found")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "用户_NOT_FOUND"
        assert "用户不存在: 123" in data["message"]
        assert data["context"]["resource_id"] == 123

    def test_validation_error_conversion(self, client):
        """Test that ValidationError is converted to 400 response."""
        response = client.get("/test/validation-error")

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert data["message"] == "虚拟IP名称已存在"

    def test_generation_failed_error_conversion(self, client):
        """Test that GenerationFailedError is converted to 500 response."""
        response = client.get("/test/generation-failed")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "GENERATION_FAILED"
        assert "图像生成失败" in data["message"]
        assert "API超时" in data["message"]

    def test_external_service_error_conversion(self, client):
        """Test that ExternalServiceError is converted to 503 response."""
        response = client.get("/test/external-service")

        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "EXTERNAL_SERVICE_ERROR"
        assert "OpenAI" in data["message"]
        assert "连接超时" in data["message"]

    def test_domain_error_with_context(self, client):
        """Test that domain error context is included in response."""
        response = client.get("/test/domain-error-with-context")

        assert response.status_code == 404
        data = response.json()
        assert data["context"]["resource_id"] == 456
        assert data["context"]["user_id"] == 123
        assert data["context"]["attempt"] == 3

    def test_successful_request_passes_through(self, client):
        """Test that successful requests pass through handler unchanged."""
        response = client.get("/test/success")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "success"


class TestMiddlewareIntegration:
    """Test middleware integration with FastAPI."""

    def test_exception_handler_registered(self, app_with_middleware):
        """Verify exception handler is properly registered."""
        # Check that exception handler is registered for DomainError
        assert DomainError in app_with_middleware.exception_handlers

    def test_multiple_errors_in_sequence(self, client):
        """Test that middleware handles multiple different errors."""
        # First request: NotFoundError
        response1 = client.get("/test/not-found")
        assert response1.status_code == 404

        # Second request: ValidationError
        response2 = client.get("/test/validation-error")
        assert response2.status_code == 400

        # Third request: Success
        response3 = client.get("/test/success")
        assert response3.status_code == 200

        # All should work independently

    def test_json_response_format(self, client):
        """Test that error responses are valid JSON."""
        response = client.get("/test/not-found")

        # Should be valid JSON
        data = response.json()

        # Should have expected structure
        assert "error" in data
        assert "message" in data
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_content_type_header(self, client):
        """Test that error responses have correct content-type."""
        response = client.get("/test/not-found")

        assert "application/json" in response.headers["content-type"]


class TestErrorLogging:
    """Test that errors are properly logged."""

    def test_domain_error_logged(self, client, caplog):
        """Test that domain errors are logged with context."""
        with caplog.at_level("WARNING"):
            client.get("/test/not-found")

        # Check that error was logged
        assert any(
            "Domain error occurred" in record.message for record in caplog.records
        )
