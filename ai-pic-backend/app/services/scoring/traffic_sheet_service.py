"""
投流表生成服务

从剧本中提炼 15/30/60 秒投流素材，生成 Traffic Sheet。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import TrafficSheet, TrafficSheetAsset
from app.utils.json_utils import extract_json_block

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = get_logger()


class TrafficSheetService:
    """投流表生成服务"""

    def __init__(self, ai_service: "AIService") -> None:
        self.ai_service = ai_service

    async def generate_traffic_sheet(
        self,
        script_content: str,
        episode_number: int,
        story: Optional[Dict[str, Any]] = None,
        episode_id: Optional[int] = None,
        episode_title: Optional[str] = None,
        episode_summary: Optional[str] = None,
        script_id: Optional[int] = None,
        scenes: Optional[List[Dict[str, Any]]] = None,
        dialogues: Optional[List[Dict[str, Any]]] = None,
        hook_plan: Optional[Dict[str, Any]] = None,
        prefer_provider: Optional[str] = None,
        prefer_model: Optional[str] = None,
    ) -> TrafficSheet:
        """
        从剧本生成投流表。

        Args:
            script_content: 剧本正文内容
            episode_number: 剧集编号
            story: 故事上下文（标题、类型、市场、微类型）
            episode_id: 剧集 ID
            episode_title: 剧集标题
            episode_summary: 剧集概要
            script_id: 剧本 ID
            scenes: 场景列表
            dialogues: 对白列表
            hook_plan: 爽点/钩子规划
            prefer_provider: 优先使用的 AI 提供商
            prefer_model: 优先使用的模型

        Returns:
            TrafficSheet: 投流表
        """
        # 构建 prompt 变量
        variables = {
            "script_content": script_content,
            "episode_number": episode_number,
            "story": story or {},
            "episode_id": episode_id,
            "episode_title": episode_title or "",
            "episode_summary": episode_summary or "",
            "script_id": script_id,
            "scenes": scenes or [],
            "dialogues": dialogues or [],
            "hook_plan": hook_plan or {},
            "current_time": datetime.utcnow().isoformat(),
        }

        # 渲染 prompt
        prompt = prompt_manager.render_prompt(
            PromptTemplate.TRAFFIC_SHEET_GENERATION.value,
            variables,
        )

        logger.info(
            "Generating traffic sheet",
            extra={
                "episode_number": episode_number,
                "story_title": story.get("title") if story else None,
                "script_length": len(script_content),
            },
        )

        # 调用 AI 服务
        ai_manager = getattr(self.ai_service, "ai_manager", None)
        if not ai_manager:
            logger.warning("AI manager unavailable, returning empty traffic sheet")
            return TrafficSheet(
                episode_id=episode_id,
                script_id=script_id,
                market_region=story.get("market_region") if story else None,
                micro_genre=story.get("micro_genre") if story else None,
                assets=[],
                generated_at=datetime.utcnow(),
            )

        schema = TrafficSheet.model_json_schema()
        resp = await ai_manager.generate_text(
            prompt=prompt,
            prefer_provider=prefer_provider,
            model=prefer_model,
            max_tokens=3000,
            temperature=0.5,
            json_schema={"name": "traffic_sheet_generation", "schema": schema},
            stream=False,
        )

        response_text = resp.data
        if isinstance(response_text, dict):
            response_text = json.dumps(response_text, ensure_ascii=False)
        if not isinstance(response_text, str):
            response_text = ""

        # 解析响应
        result = self._parse_traffic_sheet_response(
            response_text,
            episode_id=episode_id,
            script_id=script_id,
            story=story,
        )

        logger.info(
            "Traffic sheet generated",
            extra={
                "episode_number": episode_number,
                "asset_count": len(result.assets),
                "asset_15s": sum(1 for a in result.assets if a.duration_seconds == 15),
                "asset_30s": sum(1 for a in result.assets if a.duration_seconds == 30),
                "asset_60s": sum(1 for a in result.assets if a.duration_seconds == 60),
            },
        )

        return result

    def _parse_traffic_sheet_response(
        self,
        response: str,
        episode_id: Optional[int] = None,
        script_id: Optional[int] = None,
        story: Optional[Dict[str, Any]] = None,
    ) -> TrafficSheet:
        """解析 AI 响应为投流表"""
        try:
            data = extract_json_block(response)
            if not data:
                raise ValueError("No JSON found in response")

            # 解析素材列表
            assets = []
            for asset_data in data.get("assets", []):
                asset = TrafficSheetAsset(
                    asset_id=asset_data.get("asset_id", f"asset_{len(assets)+1}"),
                    duration_seconds=int(asset_data.get("duration_seconds", 15)),
                    market_region=asset_data.get("market_region"),
                    micro_genre=asset_data.get("micro_genre"),
                    hook_type=asset_data.get("hook_type", "reveal"),
                    source_episode=int(asset_data.get("source_episode", 1)),
                    source_timecode_start=asset_data.get("source_timecode_start"),
                    source_timecode_end=asset_data.get("source_timecode_end"),
                    key_line=asset_data.get("key_line", ""),
                    visual_hook=asset_data.get("visual_hook", ""),
                    shot_list=asset_data.get("shot_list", []),
                    cliff_or_cta=asset_data.get("cliff_or_cta", ""),
                    music_reference=asset_data.get("music_reference"),
                    compliance_flags=asset_data.get("compliance_flags"),
                )
                assets.append(asset)

            return TrafficSheet(
                episode_id=episode_id or data.get("episode_id"),
                script_id=script_id or data.get("script_id"),
                market_region=data.get("market_region")
                or (story.get("market_region") if story else None),
                micro_genre=data.get("micro_genre")
                or (story.get("micro_genre") if story else None),
                assets=assets,
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.warning(f"Failed to parse traffic sheet response: {e}")
            return TrafficSheet(
                episode_id=episode_id,
                script_id=script_id,
                market_region=story.get("market_region") if story else None,
                micro_genre=story.get("micro_genre") if story else None,
                assets=[],
                generated_at=datetime.utcnow(),
            )


async def generate_traffic_sheet_from_db(
    ai_service: "AIService",
    script_id: int,
    db_session: Any,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
) -> TrafficSheet:
    """
    从数据库加载剧本并生成投流表（便捷函数）。

    Args:
        ai_service: AI 服务实例
        script_id: 剧本 ID
        db_session: 数据库会话
        prefer_provider: 优先使用的 AI 提供商
        prefer_model: 优先使用的模型

    Returns:
        TrafficSheet: 投流表
    """
    from app.models.script import Script
    from app.utils.marketing_meta import merge_marketing_meta

    script = db_session.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise ValueError(f"Script {script_id} not found")

    # 加载关联的剧集和故事
    episode = getattr(script, "episode", None)
    story = getattr(episode, "story", None) if episode else None

    # 构建上下文
    story_ctx = None
    if story:
        marketing_meta = merge_marketing_meta(
            story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
            script.extra_metadata if isinstance(script.extra_metadata, dict) else {},
            (
                script.generation_params
                if isinstance(script.generation_params, dict)
                else {}
            ),
        )
        story_ctx = {
            "title": story.title,
            "genre": story.genre,
            "market_region": marketing_meta.get("market_region"),
            "micro_genre": marketing_meta.get("micro_genre"),
        }

    marketing_meta = merge_marketing_meta(
        (
            story.extra_metadata
            if story and isinstance(story.extra_metadata, dict)
            else {}
        ),
        (
            episode.extra_metadata
            if episode and isinstance(episode.extra_metadata, dict)
            else {}
        ),
        script.extra_metadata if isinstance(script.extra_metadata, dict) else {},
        script.generation_params if isinstance(script.generation_params, dict) else {},
    )
    hook_plan = marketing_meta.get("hook_plan")

    # 生成投流表
    service = TrafficSheetService(ai_service)
    return await service.generate_traffic_sheet(
        script_content=script.content or "",
        episode_number=episode.episode_number if episode else 1,
        story=story_ctx,
        episode_id=episode.id if episode else None,
        episode_title=episode.title if episode else None,
        episode_summary=episode.summary if episode else None,
        script_id=script_id,
        scenes=script.scenes or [],
        dialogues=script.dialogues or [],
        hook_plan=hook_plan,
        prefer_provider=prefer_provider,
        prefer_model=prefer_model,
    )
