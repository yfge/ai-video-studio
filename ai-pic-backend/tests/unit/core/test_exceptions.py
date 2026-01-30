"""
Tests for centralized exception hierarchy.
"""

from app.core.exceptions import (
    ConfigurationError,
    ConflictError,
    DomainError,
    DuplicateError,
    ExternalServiceError,
    ForbiddenError,
    GenerationFailedError,
    InvalidFormatError,
    MissingFieldError,
    NotFoundError,
    ServiceError,
    UnauthorizedError,
    ValidationError,
)


class TestDomainError:
    """Test base DomainError class."""

    def test_basic_error(self):
        error = DomainError("测试错误")
        assert error.message == "测试错误"
        assert error.status_code == 500
        assert error.error_code == "INTERNAL_ERROR"
        assert error.context == {}

    def test_error_with_context(self):
        error = DomainError("测试错误", context={"key": "value"})
        assert error.context == {"key": "value"}

    def test_error_with_custom_code(self):
        error = DomainError("测试错误", error_code="CUSTOM_ERROR")
        assert error.error_code == "CUSTOM_ERROR"

    def test_to_dict(self):
        error = DomainError("测试错误", context={"user_id": 123})
        result = error.to_dict()
        assert result == {
            "error": "INTERNAL_ERROR",
            "message": "测试错误",
            "context": {"user_id": 123},
        }


class TestNotFoundError:
    """Test NotFoundError class."""

    def test_basic_not_found(self):
        error = NotFoundError("用户", 123)
        assert error.message == "用户不存在: 123"
        assert error.status_code == 404
        assert error.context["resource_id"] == 123
        assert error.context["resource_type"] == "用户"

    def test_not_found_without_id(self):
        error = NotFoundError("虚拟IP")
        assert error.message == "虚拟IP不存在"
        assert "resource_id" not in error.context

    def test_not_found_custom_message(self):
        error = NotFoundError("脚本", 456, message="找不到指定脚本")
        assert error.message == "找不到指定脚本"
        assert error.context["resource_id"] == 456

    def test_user_factory(self):
        error = NotFoundError.user(123)
        assert error.message == "用户不存在: 123"
        assert error.status_code == 404

    def test_virtual_ip_factory(self):
        error = NotFoundError.virtual_ip("vip_123")
        assert error.message == "虚拟IP不存在: vip_123"

    def test_script_factory(self):
        error = NotFoundError.script(456)
        assert error.message == "脚本不存在: 456"


class TestValidationError:
    """Test ValidationError and subclasses."""

    def test_basic_validation_error(self):
        error = ValidationError("虚拟IP名称已存在")
        assert error.message == "虚拟IP名称已存在"
        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"

    def test_validation_error_with_field(self):
        error = ValidationError("格式不正确", field="email")
        assert error.context["field"] == "email"

    def test_missing_field_error(self):
        error = MissingFieldError("user_id")
        assert error.message == "缺少必填字段: user_id"
        assert error.status_code == 400
        assert error.context["field"] == "user_id"

    def test_missing_field_custom_message(self):
        error = MissingFieldError("prompt", "必须提供提示词")
        assert error.message == "必须提供提示词"

    def test_invalid_format_error(self):
        error = InvalidFormatError("scene_numbers")
        assert error.message == "字段格式不正确: scene_numbers"
        assert error.context["field"] == "scene_numbers"

    def test_invalid_format_custom_message(self):
        error = InvalidFormatError("date", "日期格式必须为YYYY-MM-DD")
        assert error.message == "日期格式必须为YYYY-MM-DD"

    def test_duplicate_error(self):
        error = DuplicateError("虚拟IP名称", "测试名称")
        assert error.message == "虚拟IP名称已存在: 测试名称"
        assert error.context["value"] == "测试名称"
        assert error.context["field"] == "虚拟IP名称"


class TestAuthErrors:
    """Test authentication and authorization errors."""

    def test_unauthorized_error(self):
        error = UnauthorizedError("令牌已过期")
        assert error.message == "令牌已过期"
        assert error.status_code == 401
        assert error.error_code == "UNAUTHORIZED"

    def test_forbidden_error(self):
        error = ForbiddenError("没有权限访问此资源")
        assert error.message == "没有权限访问此资源"
        assert error.status_code == 403
        assert error.error_code == "FORBIDDEN"

    def test_conflict_error(self):
        error = ConflictError("资源正在被使用")
        assert error.message == "资源正在被使用"
        assert error.status_code == 409


class TestServiceErrors:
    """Test server-side errors."""

    def test_service_error(self):
        error = ServiceError("内部错误")
        assert error.status_code == 500

    def test_generation_failed_basic(self):
        error = GenerationFailedError("图像", "API超时")
        assert error.message == "图像生成失败: API超时"
        assert error.context["generation_type"] == "图像"
        assert error.context["reason"] == "API超时"

    def test_generation_failed_no_reason(self):
        error = GenerationFailedError("视频")
        assert error.message == "视频生成失败"

    def test_generation_failed_image_factory(self):
        error = GenerationFailedError.image("模型返回错误")
        assert error.message == "图像生成失败: 模型返回错误"

    def test_generation_failed_factories(self):
        assert GenerationFailedError.video().message == "视频生成失败"
        assert GenerationFailedError.script().message == "脚本生成失败"
        assert GenerationFailedError.story().message == "故事生成失败"
        assert GenerationFailedError.audio().message == "音频生成失败"

    def test_configuration_error(self):
        error = ConfigurationError("OSS服务未配置")
        assert error.message == "OSS服务未配置"
        assert error.status_code == 500

    def test_external_service_error(self):
        error = ExternalServiceError("OpenAI", "连接超时")
        assert error.message == "外部服务 OpenAI 不可用: 连接超时"
        assert error.status_code == 503
        assert error.context["service_name"] == "OpenAI"
        assert error.context["reason"] == "连接超时"

    def test_external_service_no_reason(self):
        error = ExternalServiceError("Keling")
        assert error.message == "外部服务 Keling 不可用"


class TestExceptionToDict:
    """Test exception serialization."""

    def test_simple_exception_to_dict(self):
        error = NotFoundError.user(123)
        result = error.to_dict()
        assert result["error"] == "用户_NOT_FOUND"
        assert result["message"] == "用户不存在: 123"
        assert result["context"]["resource_id"] == 123

    def test_exception_without_context(self):
        error = ValidationError("测试错误")
        result = error.to_dict()
        # Context is only included if not empty
        if "context" in result:
            assert result["context"] == {}

    def test_exception_with_rich_context(self):
        error = GenerationFailedError(
            "图像", "API错误", context={"provider": "openai", "attempt": 3}
        )
        result = error.to_dict()
        assert result["context"]["provider"] == "openai"
        assert result["context"]["attempt"] == 3
        assert result["context"]["generation_type"] == "图像"
