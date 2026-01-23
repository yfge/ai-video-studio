"""
剧本评分服务

实现 HookScore/ScriptScore agent，评估短剧剧本的投流效果与制作可行性。
评分维度：冲突强度、角色辨识度、文化适配、素材可剪性、逻辑一致性（各 0-5 分）
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import (
    ScriptScoreDimensions,
    ScriptScoreResult,
)
from app.utils.json_utils import extract_json_block

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = get_logger()


# 评分阈值常量
PASS_OVERALL_THRESHOLD = 4.0
PASS_DIMENSION_THRESHOLD = 3.5
REVIEW_OVERALL_MIN = 3.5
REVIEW_DIMENSION_MIN = 3.0


class ScriptScoreService:
    """剧本评分服务"""

    def __init__(self, ai_service: "AIService") -> None:
        self.ai_service = ai_service

    async def score_script(
        self,
        script_content: str,
        story: Optional[Dict[str, Any]] = None,
        episode: Optional[Dict[str, Any]] = None,
        scenes: Optional[List[Dict[str, Any]]] = None,
        dialogues: Optional[List[Dict[str, Any]]] = None,
        prefer_provider: Optional[str] = None,
        prefer_model: Optional[str] = None,
    ) -> ScriptScoreResult:
        """
        评估剧本质量并返回评分结果。

        Args:
            script_content: 剧本正文内容
            story: 故事上下文（标题、类型、市场、微类型）
            episode: 剧集上下文（集数、标题、概要）
            scenes: 场景列表
            dialogues: 对白列表
            prefer_provider: 优先使用的 AI 提供商
            prefer_model: 优先使用的模型

        Returns:
            ScriptScoreResult: 评分结果
        """
        # 构建 prompt 变量
        variables = {
            "script_content": script_content,
            "story": story or {},
            "episode": episode or {},
            "scenes": scenes or [],
            "dialogues": dialogues or [],
        }

        # 渲染 prompt
        prompt = prompt_manager.render_prompt(
            PromptTemplate.SCRIPT_SCORE.value,
            variables,
        )

        logger.info(
            "Scoring script",
            extra={
                "story_title": story.get("title") if story else None,
                "episode_number": episode.get("episode_number") if episode else None,
                "script_length": len(script_content),
            },
        )

        # 调用 AI 服务
        response = await self.ai_service.generate_text(
            prompt=prompt,
            prefer_provider=prefer_provider,
            prefer_model=prefer_model,
            max_tokens=2000,
            temperature=0.3,  # 低温度以保持评分一致性
        )

        # 解析响应
        result = self._parse_score_response(response)

        logger.info(
            "Script scored",
            extra={
                "overall_score": result.overall_score,
                "verdict": result.verdict,
                "strengths_count": len(result.strengths),
                "risks_count": len(result.risks),
            },
        )

        return result

    def _parse_score_response(self, response: str) -> ScriptScoreResult:
        """解析 AI 响应为评分结果"""
        try:
            data = extract_json_block(response)
            if not data:
                raise ValueError("No JSON found in response")

            # 解析维度评分
            dim_data = data.get("dimension_scores", {})
            dimensions = ScriptScoreDimensions(
                conflict_intensity=float(dim_data.get("conflict_intensity", 3.0)),
                character_recognizability=float(
                    dim_data.get("character_recognizability", 3.0)
                ),
                cultural_fit=float(dim_data.get("cultural_fit", 3.0)),
                clip_ability=float(dim_data.get("clip_ability", 3.0)),
                logic_coherence=float(dim_data.get("logic_coherence", 3.0)),
            )

            # 计算总分（如果 AI 未提供）
            overall = data.get("overall_score")
            if overall is None:
                overall = (
                    dimensions.conflict_intensity
                    + dimensions.character_recognizability
                    + dimensions.cultural_fit
                    + dimensions.clip_ability
                    + dimensions.logic_coherence
                ) / 5.0

            # 判定结果（如果 AI 未提供或不准确）
            verdict = self._compute_verdict(float(overall), dimensions)

            return ScriptScoreResult(
                overall_score=float(overall),
                dimension_scores=dimensions,
                verdict=verdict,
                strengths=data.get("strengths", []),
                risks=data.get("risks", []),
                rewrite_guidance=data.get("rewrite_guidance", []),
                suggested_ad_hooks=data.get("suggested_ad_hooks", []),
            )

        except Exception as e:
            logger.warning(f"Failed to parse score response: {e}, using defaults")
            return self._default_score_result()

    def _compute_verdict(
        self, overall: float, dimensions: ScriptScoreDimensions
    ) -> str:
        """根据阈值计算判定结果"""
        min_dim = min(
            dimensions.conflict_intensity,
            dimensions.character_recognizability,
            dimensions.cultural_fit,
            dimensions.clip_ability,
            dimensions.logic_coherence,
        )

        # Pass: 总分 >= 4.0 且无任何维度 < 3.5
        if overall >= PASS_OVERALL_THRESHOLD and min_dim >= PASS_DIMENSION_THRESHOLD:
            return "pass"

        # Rewrite: 总分 < 3.5 或任一维度 < 3.0
        if overall < REVIEW_OVERALL_MIN or min_dim < REVIEW_DIMENSION_MIN:
            return "rewrite"

        # Review: 其他情况
        return "review"

    def _default_score_result(self) -> ScriptScoreResult:
        """返回默认评分结果（解析失败时使用）"""
        default_dims = ScriptScoreDimensions(
            conflict_intensity=3.0,
            character_recognizability=3.0,
            cultural_fit=3.0,
            clip_ability=3.0,
            logic_coherence=3.0,
        )
        return ScriptScoreResult(
            overall_score=3.0,
            dimension_scores=default_dims,
            verdict="review",
            strengths=[],
            risks=["评分解析失败，建议人工审核"],
            rewrite_guidance=["请重新提交评分或人工审核"],
            suggested_ad_hooks=[],
        )


async def score_script_from_db(
    ai_service: "AIService",
    script_id: int,
    db_session: Any,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
) -> ScriptScoreResult:
    """
    从数据库加载剧本并评分（便捷函数）。

    Args:
        ai_service: AI 服务实例
        script_id: 剧本 ID
        db_session: 数据库会话
        prefer_provider: 优先使用的 AI 提供商
        prefer_model: 优先使用的模型

    Returns:
        ScriptScoreResult: 评分结果
    """
    from app.models.script import Script
    from app.models.episode import Episode
    from app.models.story import Story

    # 加载剧本
    script = db_session.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise ValueError(f"Script {script_id} not found")

    # 加载关联的剧集和故事
    episode = None
    story = None
    if script.episode_id:
        episode = db_session.query(Episode).filter(Episode.id == script.episode_id).first()
        if episode and episode.story_id:
            story = db_session.query(Story).filter(Story.id == episode.story_id).first()

    # 构建上下文
    story_ctx = None
    if story:
        story_ctx = {
            "title": story.title,
            "genre": story.genre,
            "market_region": story.extra_metadata.get("market_region")
            if story.extra_metadata
            else None,
            "micro_genre": story.extra_metadata.get("micro_genre")
            if story.extra_metadata
            else None,
        }

    episode_ctx = None
    if episode:
        episode_ctx = {
            "episode_number": episode.episode_number,
            "title": episode.title,
            "summary": episode.summary,
        }

    # 解析剧本数据
    script_data = script.script_data or {}
    scenes = script_data.get("scenes", [])
    dialogues = script_data.get("dialogues", [])
    content = script_data.get("content", "")

    # 评分
    service = ScriptScoreService(ai_service)
    return await service.score_script(
        script_content=content,
        story=story_ctx,
        episode=episode_ctx,
        scenes=scenes,
        dialogues=dialogues,
        prefer_provider=prefer_provider,
        prefer_model=prefer_model,
    )
