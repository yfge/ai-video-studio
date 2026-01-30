"""FastAPI application factory.

Exposes ``app`` for tests and production entrypoints while keeping the project
package importable (``from app.main import app``).
"""

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.logging import LoggingMiddleware, setup_logging
from app.core.middleware import domain_exception_handler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

# Set up structured logging once at import time so all application instances
# share the same configuration.
logger = setup_logging(
    app_name="ai-video-studio",
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    enable_file_logging=settings.ENABLE_FILE_LOGGING,
    enable_console_logging=settings.ENABLE_CONSOLE_LOGGING,
    feishu_webhook_url=settings.FEISHU_WEBHOOK_URL,
    backup_count=settings.LOG_BACKUP_COUNT,
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI图片生成API服务",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Exception handlers (must be registered before middlewares)
    app.add_exception_handler(DomainError, domain_exception_handler)

    # Middlewares (order matters: first added = outermost layer)
    # Request logging
    app.add_middleware(LoggingMiddleware)

    # CORS and security
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # Routers & static assets
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads",
    )

    @app.get("/")
    async def root():
        logger.info("Root endpoint accessed")
        return {"message": "AI图片生成API服务", "version": settings.VERSION}

    @app.get("/health")
    async def health_check():
        logger.info("Health check endpoint accessed")
        return {"status": "healthy", "logging": "enabled"}

    return app


app = create_app()
