"""
诊断API端点

提供AI图像生成系统的诊断和测试功能
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.services.diagnostic_service import diagnostic_service

router = APIRouter()

@router.get("/health")
async def quick_health_check():
    """快速健康检查"""
    try:
        result = await diagnostic_service.quick_health_check()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.post("/full")
async def run_full_diagnostic(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """运行完整的诊断测试（需要管理员权限）"""
    try:
        result = await diagnostic_service.run_full_diagnostic()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完整诊断失败: {str(e)}")

@router.post("/openai")
async def test_openai_api(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试OpenAI API连接"""
    try:
        success = await diagnostic_service.test_openai_api()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("OpenAI API", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OpenAI API测试失败: {str(e)}"
        }

@router.post("/oss")
async def test_oss_service(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试OSS服务"""
    try:
        success = await diagnostic_service.test_oss_service()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("OSS服务", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OSS服务测试失败: {str(e)}"
        }

@router.post("/oss-image")
async def test_oss_image_upload(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试OSS图片上传（使用1x1 PNG模拟虚拟IP图像上传路径）"""
    try:
        success = await diagnostic_service.test_oss_image_upload()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("OSS图片上传", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OSS图片上传测试失败: {str(e)}"
        }

@router.post("/database")
async def test_database_connection(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试数据库连接"""
    try:
        success = await diagnostic_service.test_database_connection()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("数据库连接", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"数据库测试失败: {str(e)}"
        }

@router.post("/filesystem") 
async def test_file_system(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试文件系统"""
    try:
        success = await diagnostic_service.test_file_system()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("文件系统", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"文件系统测试失败: {str(e)}"
        }

@router.post("/end-to-end")
async def test_end_to_end_generation(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """测试端到端图像生成"""
    try:
        success = await diagnostic_service.test_end_to_end_image_generation()
        return {
            "success": success,
            "test_result": diagnostic_service.test_results.get("端到端测试", {})
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"端到端测试失败: {str(e)}"
        }
