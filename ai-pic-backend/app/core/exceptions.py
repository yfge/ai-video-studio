"""
Centralized exception hierarchy for domain-level errors.

This module provides a structured exception system that replaces scattered
HTTPException raises throughout the codebase. Domain exceptions are converted
to HTTP responses by exception middleware.

Usage:
    from app.core.exceptions import NotFoundError

    if not user:
        raise NotFoundError("用户", user_id)

The middleware will automatically convert this to:
    HTTPException(status_code=404, detail="用户不存在: {user_id}")
"""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """
    Base class for all domain-level exceptions.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (default: 500)
        error_code: Machine-readable error code for API clients
        context: Additional context data for debugging
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.context = context or {}
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.context:
            result["context"] = self.context
        return result


# ============================================================================
# 4xx Client Errors
# ============================================================================

class NotFoundError(DomainError):
    """
    Resource not found error (404).

    Usage:
        raise NotFoundError("用户", user_id)
        raise NotFoundError("虚拟IP", virtual_ip_id)
        raise NotFoundError.user(user_id)
    """

    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(
        self,
        resource_type: str,
        resource_id: Any = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            if resource_id is not None:
                message = f"{resource_type}不存在: {resource_id}"
            else:
                message = f"{resource_type}不存在"

        context = context or {}
        if resource_id is not None:
            context["resource_id"] = resource_id
        context["resource_type"] = resource_type

        super().__init__(message, context, f"{resource_type.upper()}_NOT_FOUND")

    # Convenience factory methods for common resources
    @classmethod
    def user(cls, user_id: Any) -> "NotFoundError":
        return cls("用户", user_id)

    @classmethod
    def virtual_ip(cls, virtual_ip_id: Any) -> "NotFoundError":
        return cls("虚拟IP", virtual_ip_id)

    @classmethod
    def script(cls, script_id: Any) -> "NotFoundError":
        return cls("脚本", script_id)

    @classmethod
    def episode(cls, episode_id: Any) -> "NotFoundError":
        return cls("剧集", episode_id)

    @classmethod
    def story(cls, story_id: Any) -> "NotFoundError":
        return cls("故事", story_id)

    @classmethod
    def scene(cls, scene_id: Any) -> "NotFoundError":
        return cls("场景", scene_id)

    @classmethod
    def shot(cls, shot_id: Any) -> "NotFoundError":
        return cls("镜头", shot_id)

    @classmethod
    def beat(cls, beat_id: Any) -> "NotFoundError":
        return cls("节拍", beat_id)

    @classmethod
    def environment(cls, env_id: Any) -> "NotFoundError":
        return cls("环境", env_id)

    @classmethod
    def image(cls, image_id: Any) -> "NotFoundError":
        return cls("图像", image_id)


class ValidationError(DomainError):
    """
    Input validation error (400).

    Usage:
        raise ValidationError("虚拟IP名称已存在")
        raise ValidationError("必须提供prompt或image_url", field="prompt")
    """

    status_code = 400
    error_code = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        context = context or {}
        if field:
            context["field"] = field
        super().__init__(message, context)


class MissingFieldError(ValidationError):
    """
    Required field missing error (400).

    Usage:
        raise MissingFieldError("user_id")
        raise MissingFieldError("prompt", "必须提供提示词")
    """

    error_code = "MISSING_FIELD"

    def __init__(
        self,
        field: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"缺少必填字段: {field}"
        super().__init__(message, field, context)


class InvalidFormatError(ValidationError):
    """
    Invalid format error (400).

    Usage:
        raise InvalidFormatError("scene_numbers", "必须是数组格式")
    """

    error_code = "INVALID_FORMAT"

    def __init__(
        self,
        field: str,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"字段格式不正确: {field}"
        super().__init__(message, field, context)


class DuplicateError(ValidationError):
    """
    Duplicate resource error (400).

    Usage:
        raise DuplicateError("虚拟IP名称", name)
    """

    error_code = "DUPLICATE"

    def __init__(
        self,
        resource_type: str,
        value: Any,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"{resource_type}已存在: {value}"
        context = context or {}
        context["value"] = value
        super().__init__(message, resource_type, context)


class UnauthorizedError(DomainError):
    """
    Authentication required error (401).

    Usage:
        raise UnauthorizedError("令牌已过期")
    """

    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(DomainError):
    """
    Permission denied error (403).

    Usage:
        raise ForbiddenError("没有权限访问此资源")
    """

    status_code = 403
    error_code = "FORBIDDEN"


class ConflictError(DomainError):
    """
    Resource conflict error (409).

    Usage:
        raise ConflictError("资源正在被其他操作使用")
    """

    status_code = 409
    error_code = "CONFLICT"


# ============================================================================
# 5xx Server Errors
# ============================================================================

class ServiceError(DomainError):
    """
    Internal service error (500).

    Base class for server-side errors.
    """

    status_code = 500
    error_code = "SERVICE_ERROR"


class GenerationFailedError(ServiceError):
    """
    AI generation failed error (500).

    Usage:
        raise GenerationFailedError("图像生成", "API返回错误")
        raise GenerationFailedError.image("模型超时")
    """

    error_code = "GENERATION_FAILED"

    def __init__(
        self,
        generation_type: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        message = f"{generation_type}生成失败"
        if reason:
            message += f": {reason}"

        context = context or {}
        context["generation_type"] = generation_type
        if reason:
            context["reason"] = reason

        super().__init__(message, context)

    @classmethod
    def image(cls, reason: Optional[str] = None) -> "GenerationFailedError":
        return cls("图像", reason)

    @classmethod
    def video(cls, reason: Optional[str] = None) -> "GenerationFailedError":
        return cls("视频", reason)

    @classmethod
    def script(cls, reason: Optional[str] = None) -> "GenerationFailedError":
        return cls("脚本", reason)

    @classmethod
    def story(cls, reason: Optional[str] = None) -> "GenerationFailedError":
        return cls("故事", reason)

    @classmethod
    def audio(cls, reason: Optional[str] = None) -> "GenerationFailedError":
        return cls("音频", reason)


class ConfigurationError(ServiceError):
    """
    Service configuration error (500).

    Usage:
        raise ConfigurationError("OSS服务未配置")
    """

    error_code = "CONFIGURATION_ERROR"


class ExternalServiceError(DomainError):
    """
    External service unavailable error (503).

    Usage:
        raise ExternalServiceError("OpenAI", "API超时")
    """

    status_code = 503
    error_code = "EXTERNAL_SERVICE_ERROR"

    def __init__(
        self,
        service_name: str,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        message = f"外部服务 {service_name} 不可用"
        if reason:
            message += f": {reason}"

        context = context or {}
        context["service_name"] = service_name
        if reason:
            context["reason"] = reason

        super().__init__(message, context)
