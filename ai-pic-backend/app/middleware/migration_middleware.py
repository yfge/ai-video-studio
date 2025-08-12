"""
迁移中间件

在应用启动时检查数据库迁移状态，并在需要时提醒管理员
"""

import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.migrations import migration_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class MigrationCheckMiddleware(BaseHTTPMiddleware):
    """迁移检查中间件"""
    
    def __init__(self, app, check_on_startup: bool = True, require_up_to_date: bool = False):
        super().__init__(app)
        self.check_on_startup = check_on_startup
        self.require_up_to_date = require_up_to_date
        self._migration_status_checked = False
        self._migration_status = None
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        
        # 在首次请求时检查迁移状态
        if not self._migration_status_checked and self.check_on_startup:
            await self._check_migration_status()
        
        # 如果要求数据库必须是最新的，且不是最新的，则阻止访问
        if (self.require_up_to_date and 
            self._migration_status and 
            not self._migration_status.get('is_up_to_date', True)):
            
            # 允许访问迁移相关的API端点
            if request.url.path.startswith(f"{settings.API_V1_STR}/migrations"):
                return await call_next(request)
            
            # 允许访问健康检查端点
            if request.url.path in ["/health", "/", f"{settings.API_V1_STR}/health"]:
                return await call_next(request)
            
            # 返回数据库需要升级的错误
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "数据库需要升级",
                    "migration_status": self._migration_status,
                    "migration_endpoint": f"{settings.API_V1_STR}/migrations/status"
                }
            )
        
        # 在响应头中添加迁移状态信息
        response = await call_next(request)
        
        if self._migration_status:
            response.headers["X-Migration-Status"] = (
                "up-to-date" if self._migration_status.get('is_up_to_date') else "needs-upgrade"
            )
            if self._migration_status.get('current_revision'):
                response.headers["X-Migration-Current"] = self._migration_status['current_revision']
        
        return response
    
    async def _check_migration_status(self):
        """检查迁移状态"""
        try:
            self._migration_status = migration_manager.check_migration_status()
            self._migration_status_checked = True
            
            if not self._migration_status.get('database_exists'):
                logger.warning("数据库不存在或无法连接")
            elif not self._migration_status.get('is_up_to_date'):
                pending_count = self._migration_status.get('pending_count', 0)
                logger.warning(f"数据库需要升级，有 {pending_count} 个待应用的迁移")
            else:
                logger.info("数据库迁移状态正常")
                
        except Exception as e:
            logger.error(f"检查迁移状态失败: {e}")
            self._migration_status = {
                "error": str(e),
                "database_exists": False,
                "is_up_to_date": False
            }
            self._migration_status_checked = True

class DatabaseHealthMiddleware(BaseHTTPMiddleware):
    """数据库健康检查中间件"""
    
    def __init__(self, app, health_check_interval: int = 300):  # 5分钟检查一次
        super().__init__(app)
        self.health_check_interval = health_check_interval
        self._last_health_check = 0
        self._database_healthy = True
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        import time
        
        current_time = time.time()
        
        # 定期检查数据库健康状态
        if current_time - self._last_health_check > self.health_check_interval:
            await self._check_database_health()
            self._last_health_check = current_time
        
        # 如果数据库不健康，返回503错误
        if not self._database_healthy:
            # 允许访问健康检查端点
            if request.url.path in ["/health", "/", f"{settings.API_V1_STR}/migrations/health"]:
                return await call_next(request)
            
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "数据库连接不可用",
                    "health_check_endpoint": f"{settings.API_V1_STR}/migrations/health"
                }
            )
        
        response = await call_next(request)
        response.headers["X-Database-Health"] = "healthy" if self._database_healthy else "unhealthy"
        
        return response
    
    async def _check_database_health(self):
        """检查数据库健康状态"""
        try:
            status = migration_manager.check_migration_status()
            self._database_healthy = status.get('database_exists', False)
            
            if not self._database_healthy:
                logger.warning("数据库健康检查失败")
            
        except Exception as e:
            logger.error(f"数据库健康检查异常: {e}")
            self._database_healthy = False