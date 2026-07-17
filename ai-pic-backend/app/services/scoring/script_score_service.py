"""
剧本评分服务

实现 HookScore/ScriptScore agent，评估短剧剧本的投流效果与制作可行性。
评分维度：冲突强度、角色辨识度、文化适配、素材可剪性、逻辑一致性（各 0-5 分）
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import ScriptScoreDimensions, ScriptScoreResult
from app.services.scoring.script_score_schema import script_score_json_schema
from app.services.script_score_thresholds import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
    REVIEW_DIMENSION_MIN,
    REVIEW_OVERALL_MIN,
)
from app.utils.json_utils import extract_json_block

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = get_logger()


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
        requirements: Optional[str] = None,
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
            requirements: 原始目标与生产约束
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
            "requirements": requirements or "",
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
                "requirements_length": len(requirements or ""),
            },
        )

        # 调用 AI 服务
        ai_manager = getattr(self.ai_service, "ai_manager", None)
        if not ai_manager:
            logger.warning("AI manager unavailable, returning default score result")
            return self._default_score_result()

        resp = await ai_manager.generate_text(
            prompt=prompt,
            prefer_provider=prefer_provider,
            model=prefer_model,
            max_tokens=2000,
            temperature=0.3,  # 低温度以保持评分一致性
            json_schema={"name": "script_score", "schema": script_score_json_schema()},
            stream=False,
        )

        response_text = resp.data
        if isinstance(response_text, dict):
            response_text = json.dumps(response_text, ensure_ascii=False)
        if not isinstance(response_text, str):
            response_text = ""

        # 解析响应
        result = self._parse_score_response(response_text)

        logger.info(
            "Script scored",
            extra={
                "overall_score": result.overall_score,
                "verdict": result.verdict,
                "strengths_count": len(result.strengths),
                "risks_count": len(result.risks),
                "provider_used": getattr(resp, "provider", None),
                "model_used": getattr(resp, "model", None),
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
