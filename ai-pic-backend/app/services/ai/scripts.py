from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.services.continuity.script_continuity import (
    run_script_continuity_audit,
    run_script_dialogues_rewrite_with_audit,
)
from app.utils.json_utils import extract_json_block

if TYPE_CHECKING:
    from app.services.duration_orchestrator.state import SceneBudget

_SCRIPT_AGENT_TIMEOUT_SECONDS = 120


class ScriptGenerationMixin:
    async def generate_script(
        self,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str = "screenplay",
        language: str = "zh-CN",
        dialogue_style: str = "natural",
        scene_detail_level: str = "medium",
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        scene_budgets: Optional[List[SceneBudget]] = None,
    ) -> Optional[Dict[str, Any]]:
        """基于剧集信息生成详细剧本"""
        continuity_ledger = (
            story.get("continuity_ledger") if isinstance(story, dict) else None
        )

        async def _maybe_apply_script_continuity_rewrite(payload: Dict[str, Any]) -> None:
            ai_manager = getattr(self, "ai_manager", None)
            if not ai_manager:
                return
            scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
            dialogues = (
                payload.get("dialogues") if isinstance(payload.get("dialogues"), list) else []
            )
            stage_directions = (
                payload.get("stage_directions")
                if isinstance(payload.get("stage_directions"), list)
                else []
            )
            if not scenes:
                return
            try:
                audit, _ = await run_script_continuity_audit(
                    ai_manager=ai_manager,
                    story=story,
                    episode=episode,
                    continuity_ledger=continuity_ledger,
                    scenes=scenes,
                    dialogues=dialogues,
                    stage_directions=stage_directions,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                if audit.verdict != "fail" or not audit.issues:
                    return
                rewrite_payload, _ = await run_script_dialogues_rewrite_with_audit(
                    ai_manager=ai_manager,
                    story=story,
                    episode=episode,
                    continuity_ledger=continuity_ledger,
                    scenes=scenes,
                    dialogues=dialogues,
                    stage_directions=stage_directions,
                    audit_issues=[issue.model_dump() for issue in audit.issues],
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                )
                new_dialogues = (
                    rewrite_payload.get("dialogues")
                    if isinstance(rewrite_payload.get("dialogues"), list)
                    else None
                )
                new_stage = (
                    rewrite_payload.get("stage_directions")
                    if isinstance(rewrite_payload.get("stage_directions"), list)
                    else None
                )
                new_scenes = (
                    rewrite_payload.get("scenes")
                    if isinstance(rewrite_payload.get("scenes"), list)
                    else None
                )
                if new_scenes is not None:
                    payload["scenes"] = new_scenes
                if new_dialogues is not None:
                    payload["dialogues"] = new_dialogues
                if new_stage is not None:
                    payload["stage_directions"] = new_stage
                payload.setdefault("metadata", {})
                if isinstance(payload["metadata"], dict):
                    payload["metadata"]["continuity_rewrite"] = {
                        "verdict": audit.verdict,
                        "issue_count": len(audit.issues),
                    }
            except Exception as exc:
                self.logger.warning(
                    "Script continuity rewrite failed",
                    extra={"error": str(exc)},
                )

        # 1) LangGraph agent
        if self.script_agent:
            try:
                duration_minutes = None if scene_budgets else 0
                coro = self.script_agent.generate(
                    episode=episode,
                    story=story,
                    format_type=format_type,
                    language=language,
                    dialogue_style=dialogue_style,
                    scene_detail_level=scene_detail_level,
                    additional_requirements=additional_requirements,
                    style_preferences=style_preferences,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    scene_budgets=scene_budgets,
                    duration_minutes=duration_minutes,
                )
                lg = await asyncio.wait_for(coro, timeout=_SCRIPT_AGENT_TIMEOUT_SECONDS)
                if lg and lg.get("content"):
                    await _maybe_apply_script_continuity_rewrite(lg["content"])
                    # 组装 content 文本
                    assembled = self._build_script_text(
                        lg["content"].get("scenes") or [],
                        lg["content"].get("dialogues") or [],
                        lg["content"].get("stage_directions") or [],
                        format_type=format_type,
                        language=language,
                    )
                    lg["content"]["content"] = assembled
                    return lg
            except asyncio.TimeoutError:
                self.logger.warning(
                    "LangGraph script agent timed out, falling back to direct generation"
                )
            except Exception as exc:
                self.logger.warning(f"LangGraph script agent failed: {exc}")

        # 2) AI 管理器直接生成
        direct = await self._call_ai_manager_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        if direct:
            # 尝试解析填充 content 以便前端展示
            parsed = direct.get("normalized") if isinstance(direct, dict) else None
            if not parsed:
                raw_content = (
                    direct.get("content") if isinstance(direct, dict) else None
                )
                if isinstance(raw_content, dict):
                    parsed = raw_content
                elif isinstance(raw_content, str):
                    parsed = extract_json_block(raw_content)

            if isinstance(parsed, dict):
                await _maybe_apply_script_continuity_rewrite(parsed)
                assembled = self._build_script_text(
                    parsed.get("scenes") or [],
                    parsed.get("dialogues") or [],
                    parsed.get("stage_directions") or [],
                    format_type=format_type,
                    language=language,
                )
                parsed["content"] = assembled
                direct["content"] = parsed
                direct["normalized"] = parsed
            return direct

        # 3) Mock 回退
        if prefer_provider or model:
            self.logger.warning(
                "Script generation failed for explicit provider/model; skip mock fallback",
                extra={
                    "prefer_provider": prefer_provider,
                    "model": model,
                    "story_format": story.get("story_format") if isinstance(story, dict) else None,
                    "episode_number": episode.get("episode_number") if isinstance(episode, dict) else None,
                },
            )
            return None
        return await self._generate_mock_script(
            episode=episode,
            story=story,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
        )

    def _build_script_text(
        self,
        scenes: List[Dict[str, Any]],
        dialogues: List[Dict[str, Any]],
        stage_directions: List[Dict[str, Any]],
        format_type: str,
        language: str,
    ) -> str:
        """简单拼装剧本文本，便于前端展示；真实文本可后续细化。"""
        lines: List[str] = [f"# {format_type} ({language})"]
        if scenes:
            lines.append("## 场景")
            for sc in scenes:
                slug = sc.get("slug_line") or f"Scene {sc.get('scene_number')}"
                summary = sc.get("summary") or sc.get("description") or ""
                lines.append(f"- {slug}: {summary}")
        if dialogues:
            lines.append("\n## 对白")
            for dlg in dialogues[:200]:
                scene_no = dlg.get("scene_number") or "-"
                char = dlg.get("character") or "旁白"
                content = dlg.get("content") or dlg.get("line") or dlg.get("text") or ""
                lines.append(f"[场景 {scene_no}] {char}: {content}")
        if stage_directions:
            lines.append("\n## 舞台指示")
            for sd in stage_directions[:200]:
                scene_no = sd.get("scene_number") or "-"
                content = (
                    sd.get("content")
                    or sd.get("direction")
                    or sd.get("description")
                    or ""
                )
                timing = sd.get("timing") or ""
                lines.append(f"[场景 {scene_no}][{timing}] {content}")
        return "\n".join(lines)
