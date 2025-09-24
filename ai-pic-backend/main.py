from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import os

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging, LoggingMiddleware, get_logger

# 初始化日志系统
logger = setup_logging(
    app_name="ai-video-studio",
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    enable_file_logging=settings.ENABLE_FILE_LOGGING,
    enable_console_logging=settings.ENABLE_CONSOLE_LOGGING,
    feishu_webhook_url=settings.FEISHU_WEBHOOK_URL,
    backup_count=settings.LOG_BACKUP_COUNT
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI图片生成API服务",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加日志中间件（需要在其他中间件之前）
app.add_middleware(LoggingMiddleware)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态文件：对外提供上传目录（/uploads）
# 这样前端可以直接使用 http://<backend>/uploads/xxx 访问本地存储的图片
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "AI图片生成API服务", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "logging": "enabled"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
