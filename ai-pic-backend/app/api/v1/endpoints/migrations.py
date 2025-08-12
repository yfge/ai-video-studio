"""
数据库迁移API端点

提供通过API访问迁移状态和管理功能
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.core.migrations import migration_manager, data_seeder, MigrationError
from app.core.config import settings

router = APIRouter()

# 响应模型
class MigrationStatusResponse(BaseModel):
    """迁移状态响应"""
    current_revision: str | None
    head_revision: str | None
    is_up_to_date: bool
    needs_upgrade: bool
    database_exists: bool
    pending_migrations: List[str] | None = None
    pending_count: int | None = None

class MigrationHistoryItem(BaseModel):
    """迁移历史项"""
    revision: str
    down_revision: str | None
    message: str | None
    branch_labels: str | None
    depends_on: str | None
    create_date: str | None

class ValidationResult(BaseModel):
    """验证结果"""
    valid: bool
    errors: List[str]
    warnings: List[str]

class SchemaDiff(BaseModel):
    """模式差异"""
    has_changes: bool
    changes: List[str]
    change_count: int
    error: str | None = None

class OperationResult(BaseModel):
    """操作结果"""
    success: bool
    message: str
    details: Dict[str, Any] | None = None

# 依赖函数
def check_admin_permission():
    """检查管理员权限（示例，实际应根据认证系统实现）"""
    # TODO: 实现实际的权限检查
    # 在生产环境中，这里应该检查用户是否有数据库管理权限
    pass

@router.get("/status", response_model=MigrationStatusResponse)
async def get_migration_status():
    """获取数据库迁移状态"""
    try:
        status = migration_manager.check_migration_status()
        return MigrationStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取迁移状态失败: {str(e)}")

@router.get("/history", response_model=List[MigrationHistoryItem])
async def get_migration_history():
    """获取迁移历史"""
    try:
        history = migration_manager.get_migration_history()
        return [MigrationHistoryItem(**item) for item in history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取迁移历史失败: {str(e)}")

@router.get("/validate", response_model=ValidationResult)
async def validate_migrations():
    """验证迁移文件完整性"""
    try:
        validation = migration_manager.validate_migrations()
        return ValidationResult(**validation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证迁移失败: {str(e)}")

@router.get("/schema-diff", response_model=SchemaDiff)
async def get_schema_diff():
    """获取当前数据库与模型的差异"""
    try:
        diff = migration_manager.get_schema_diff()
        return SchemaDiff(**diff)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模式差异失败: {str(e)}")

@router.post("/upgrade", response_model=OperationResult)
async def upgrade_database(
    background_tasks: BackgroundTasks,
    revision: str = "head",
    backup: bool = True,
    _: None = Depends(check_admin_permission)
):
    """升级数据库（后台任务）"""
    try:
        # 检查当前状态
        status = migration_manager.check_migration_status()
        
        if not status['needs_upgrade'] and revision == 'head':
            return OperationResult(
                success=True,
                message="数据库已是最新版本",
                details=status
            )
        
        # 验证迁移文件
        validation = migration_manager.validate_migrations()
        if not validation['valid']:
            raise HTTPException(
                status_code=400, 
                detail=f"迁移文件验证失败: {'; '.join(validation['errors'])}"
            )
        
        # 在后台执行升级
        def perform_upgrade():
            try:
                if backup and "mysql" in settings.DATABASE_URL:
                    migration_manager.backup_before_migration()
                
                migration_manager.upgrade(revision)
            except Exception as e:
                # 这里可以记录错误日志或发送通知
                print(f"后台升级失败: {e}")
        
        background_tasks.add_task(perform_upgrade)
        
        return OperationResult(
            success=True,
            message=f"数据库升级任务已启动，目标版本: {revision}",
            details={"current_revision": status['current_revision'], "target_revision": revision}
        )
        
    except MigrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"升级数据库失败: {str(e)}")

@router.post("/create-migration", response_model=OperationResult)
async def create_migration(
    message: str,
    autogenerate: bool = True,
    _: None = Depends(check_admin_permission)
):
    """创建新的迁移文件"""
    try:
        if not message.strip():
            raise HTTPException(status_code=400, detail="迁移描述不能为空")
        
        revision = migration_manager.create_migration(message, autogenerate)
        
        # 获取模式差异信息
        diff = migration_manager.get_schema_diff() if autogenerate else None
        
        return OperationResult(
            success=True,
            message=f"迁移创建成功: {message}",
            details={
                "revision": revision,
                "message": message,
                "autogenerate": autogenerate,
                "schema_diff": diff
            }
        )
        
    except MigrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建迁移失败: {str(e)}")

@router.post("/stamp", response_model=OperationResult)
async def stamp_revision(
    revision: str,
    _: None = Depends(check_admin_permission)
):
    """标记数据库版本"""
    try:
        migration_manager.stamp(revision)
        
        return OperationResult(
            success=True,
            message=f"版本标记成功: {revision}",
            details={"revision": revision}
        )
        
    except MigrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"版本标记失败: {str(e)}")

# 健康检查端点
@router.get("/health")
async def migration_health_check():
    """迁移系统健康检查"""
    try:
        status = migration_manager.check_migration_status()
        validation = migration_manager.validate_migrations()
        
        health_status = {
            "database_connected": status['database_exists'],
            "migrations_valid": validation['valid'],
            "up_to_date": status['is_up_to_date'],
            "system_healthy": (
                status['database_exists'] and 
                validation['valid'] and 
                status['is_up_to_date']
            )
        }
        
        return {
            "status": "healthy" if health_status["system_healthy"] else "degraded",
            "checks": health_status,
            "timestamp": status.get('timestamp', 'unknown')
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "unknown"
        }

# 开发环境特殊端点（生产环境应禁用）
@router.post("/reset-database", response_model=OperationResult)
async def reset_database(
    confirm: bool = False,
    _: None = Depends(check_admin_permission)
):
    """重置数据库（危险操作，仅开发环境）"""
    if settings.PROJECT_NAME != "AI图片生成API" or not confirm:
        raise HTTPException(
            status_code=403, 
            detail="此操作仅在开发环境可用且需要确认"
        )
    
    try:
        # 先备份
        backup_file = migration_manager.backup_before_migration()
        
        # 降级到base
        migration_manager.downgrade("base")
        
        # 重新升级
        migration_manager.upgrade("head")
        
        return OperationResult(
            success=True,
            message="数据库重置成功",
            details={
                "backup_file": backup_file,
                "new_status": migration_manager.check_migration_status()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库重置失败: {str(e)}")

# 数据种子相关端点
@router.post("/seeds/run", response_model=OperationResult)
async def run_seed(
    seed_name: str | None = None,
    run_all: bool = False,
    _: None = Depends(check_admin_permission)
):
    """运行数据种子"""
    try:
        if run_all:
            count = data_seeder.run_all_seeds()
            return OperationResult(
                success=True,
                message=f"成功运行 {count} 个种子",
                details={"seeds_count": count}
            )
        elif seed_name:
            data_seeder.run_seed(seed_name)
            return OperationResult(
                success=True,
                message=f"种子运行成功: {seed_name}",
                details={"seed_name": seed_name}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="请指定种子名称或设置 run_all=true"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"运行种子失败: {str(e)}")

@router.get("/info")
async def get_migration_info():
    """获取迁移系统信息"""
    return {
        "database_url": settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else "hidden",
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "migration_system": "Custom FastAPI Migration System",
        "alembic_integration": True,
        "features": [
            "Auto-migration generation",
            "Data seeding",
            "Schema validation",
            "Backup integration",
            "API management",
            "CLI tools"
        ]
    }