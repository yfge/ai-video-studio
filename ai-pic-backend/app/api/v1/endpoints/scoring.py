"""
剧本评分与投流表 API 端点

提供 HookScore/ScriptScore 评分接口和 Traffic Sheet 生成接口。
"""

from typing import Optional

from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.generation import ScriptScoreResult, TrafficSheet
from app.services.scoring import ScriptScoreService, TrafficSheetService
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = get_logger()
router = APIRouter()


# ========== Request/Response Schemas ==========


class ScoreScriptRequest(BaseModel):
    """剧本评分请求"""

    script_id: Optional[int] = Field(None, description="剧本 ID（从数据库加载）")
    script_content: Optional[str] = Field(None, description="剧本内容（直接传入）")
    story_title: Optional[str] = Field(None, description="故事标题")
    story_genre: Optional[str] = Field(None, description="故事类型")
    market_region: Optional[str] = Field(None, description="目标市场")
    micro_genre: Optional[str] = Field(None, description="微类型")
    episode_number: Optional[int] = Field(None, description="剧集编号")
    episode_title: Optional[str] = Field(None, description="剧集标题")
    prefer_provider: Optional[str] = Field(None, description="优先使用的 AI 提供商")
    prefer_model: Optional[str] = Field(None, description="优先使用的模型")


class GenerateTrafficSheetRequest(BaseModel):
    """投流表生成请求"""

    script_id: Optional[int] = Field(None, description="剧本 ID（从数据库加载）")
    script_content: Optional[str] = Field(None, description="剧本内容（直接传入）")
    episode_number: int = Field(..., description="剧集编号")
    episode_id: Optional[int] = Field(None, description="剧集 ID")
    episode_title: Optional[str] = Field(None, description="剧集标题")
    episode_summary: Optional[str] = Field(None, description="剧集概要")
    story_title: Optional[str] = Field(None, description="故事标题")
    story_genre: Optional[str] = Field(None, description="故事类型")
    market_region: Optional[str] = Field(None, description="目标市场")
    micro_genre: Optional[str] = Field(None, description="微类型")
    prefer_provider: Optional[str] = Field(None, description="优先使用的 AI 提供商")
    prefer_model: Optional[str] = Field(None, description="优先使用的模型")


# ========== Endpoints ==========


@router.post("/score", response_model=ScriptScoreResult)
async def score_script(
    request: ScoreScriptRequest,
    db: Session = Depends(get_db),
) -> ScriptScoreResult:
    """
    评估剧本质量。

    评分维度：
    - 冲突强度 (0-5)
    - 角色辨识度 (0-5)
    - 文化适配 (0-5)
    - 素材可剪性 (0-5)
    - 逻辑一致性 (0-5)

    判定阈值：
    - Pass: 总分 >= 4.0 且无维度 < 3.5
    - Review: 总分 3.5-3.9 或任一维度 3.0-3.4
    - Rewrite: 总分 < 3.5 或任一维度 < 3.0
    """
    # 必须提供 script_id 或 script_content
    if not request.script_id and not request.script_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 script_id 或 script_content",
        )

    from app.services.ai_service import ai_service

    score_service = ScriptScoreService(ai_service)

    # 如果提供了 script_id，从数据库加载
    if request.script_id:
        from app.services.scoring import score_script_from_db

        try:
            result = await score_script_from_db(
                ai_service=ai_service,
                script_id=request.script_id,
                db_session=db,
                prefer_provider=request.prefer_provider,
                prefer_model=request.prefer_model,
            )
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    # 使用直接传入的内容
    story_ctx = None
    if request.story_title or request.story_genre or request.market_region:
        story_ctx = {
            "title": request.story_title,
            "genre": request.story_genre,
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
        }

    episode_ctx = None
    if request.episode_number or request.episode_title:
        episode_ctx = {
            "episode_number": request.episode_number,
            "title": request.episode_title,
        }

    result = await score_service.score_script(
        script_content=request.script_content,
        story=story_ctx,
        episode=episode_ctx,
        prefer_provider=request.prefer_provider,
        prefer_model=request.prefer_model,
    )

    return result


@router.post("/traffic-sheet", response_model=TrafficSheet)
async def generate_traffic_sheet(
    request: GenerateTrafficSheetRequest,
    db: Session = Depends(get_db),
) -> TrafficSheet:
    """
    从剧本生成投流表（Traffic Sheet）。

    生成 15/30/60 秒投流素材，包含：
    - asset_id: 素材唯一标识
    - duration_seconds: 时长
    - hook_type: 钩子类型
    - key_line: 字幕锚点
    - visual_hook: 视觉钩子
    - shot_list: 关键镜头列表
    - cliff_or_cta: 卡点/CTA 文案

    目标：每 10 集产出 15s 12-20 条 + 30s 6-10 条 + 60s 2-4 条
    """
    # 必须提供 script_id 或 script_content
    if not request.script_id and not request.script_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 script_id 或 script_content",
        )

    from app.services.ai_service import ai_service

    traffic_service = TrafficSheetService(ai_service)

    # 如果提供了 script_id，从数据库加载
    if request.script_id:
        from app.services.scoring import generate_traffic_sheet_from_db

        try:
            result = await generate_traffic_sheet_from_db(
                ai_service=ai_service,
                script_id=request.script_id,
                db_session=db,
                prefer_provider=request.prefer_provider,
                prefer_model=request.prefer_model,
            )
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    # 使用直接传入的内容
    story_ctx = None
    if request.story_title or request.story_genre or request.market_region:
        story_ctx = {
            "title": request.story_title,
            "genre": request.story_genre,
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
        }

    result = await traffic_service.generate_traffic_sheet(
        script_content=request.script_content,
        episode_number=request.episode_number,
        story=story_ctx,
        episode_id=request.episode_id,
        episode_title=request.episode_title,
        episode_summary=request.episode_summary,
        prefer_provider=request.prefer_provider,
        prefer_model=request.prefer_model,
    )

    return result


@router.get("/score/{script_id}", response_model=ScriptScoreResult)
async def get_script_score(
    script_id: int,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ScriptScoreResult:
    """
    根据剧本 ID 获取评分（便捷接口）。
    """
    from app.services.ai_service import ai_service
    from app.services.scoring import score_script_from_db

    try:
        result = await score_script_from_db(
            ai_service=ai_service,
            script_id=script_id,
            db_session=db,
            prefer_provider=prefer_provider,
            prefer_model=prefer_model,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/traffic-sheet/{script_id}", response_model=TrafficSheet)
async def get_traffic_sheet(
    script_id: int,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
    db: Session = Depends(get_db),
) -> TrafficSheet:
    """
    根据剧本 ID 生成投流表（便捷接口）。
    """
    from app.services.ai_service import ai_service
    from app.services.scoring import generate_traffic_sheet_from_db

    try:
        result = await generate_traffic_sheet_from_db(
            ai_service=ai_service,
            script_id=script_id,
            db_session=db,
            prefer_provider=prefer_provider,
            prefer_model=prefer_model,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
