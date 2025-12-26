from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import ScriptModel
from app.services.duration_orchestrator.state import SceneBudget
from app.utils.json_utils import extract_json_block

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


class ScriptLangGraphAgent:
    """
    LangGraph-based pipeline to generate scripts with separate agents:
    - scene_plan: produce structured scenes list
    - dialogue: expand scenes with dialogues and stage directions
    - review: check and fix misclassified dialogues/stage_directions
    - assemble: merge + validate ScriptModel
    """

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()

    def _build_word_count_constraints(
        self,
        scene_budgets: List[SceneBudget],
        scenes: List[Dict[str, Any]],
    ) -> str:
        """Build word count constraint text for dialogue generation prompt.

        Args:
            scene_budgets: List of SceneBudget objects with target word counts.
            scenes: List of scenes from scene_plan node.

        Returns:
            Rendered constraint text to be appended to the dialogue prompt.
        """
        if not scene_budgets:
            return ""

        # Build per-scene constraints
        scene_constraints = []
        for budget in scene_budgets:
            scene_constraints.append(
                prompt_manager.render_prompt(
                    PromptTemplate.SCRIPT_WORD_COUNT_CONSTRAINT.value,
                    {
                        "scene_number": budget.scene_number,
                        "target_duration_seconds": budget.target_duration_seconds,
                        "target_word_count": budget.target_word_count,
                        "min_duration_seconds": budget.min_duration_seconds,
                        "max_duration_seconds": budget.max_duration_seconds,
                        "is_retry": budget.attempt_count > 0,
                        "attempt_number": budget.attempt_count + 1,
                        "adjustment_hint": budget.adjustment_hint or "",
                    },
                )
            )

        # Combine all scene constraints
        combined = "\n\n---\n\n".join(
            [f"### 场景 {i+1} 字数约束\n\n{c}" for i, c in enumerate(scene_constraints)]
        )

        return f"\n\n## 各场景字数约束\n\n{combined}"

    async def generate(
        self,
        *,
        episode: Dict[str, Any],
        story: Dict[str, Any],
        format_type: str,
        language: str,
        dialogue_style: str,
        scene_detail_level: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[List[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
        scene_budgets: Optional[List[SceneBudget]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        graph = StateGraph(dict)

        async def plan_scenes(state: Dict[str, Any]) -> Dict[str, Any]:
            prompt = prompt_manager.render_prompt(
                PromptTemplate.SCRIPT_SCENES.value,
                {
                    "episode": episode,
                    "story": story,
                    "scene_detail_level": scene_detail_level,
                    "format_type": format_type,
                    "language": language,
                    "style_preferences": style_preferences or [],
                    "additional_requirements": additional_requirements or "",
                },
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=min(0.6, temperature),
                model=model,
                prefer_provider=prefer_provider,
                json_schema={
                    "name": "script_scenes",
                    "schema": {
                        "type": "object",
                        "properties": {"scenes": {"type": "array"}},
                    },
                },
                system_prompt="你是专业的剧本场景规划师，请严格按 JSON 返回。",
            )
            if not resp.success:
                return {
                    "error": "scene_plan_failed",
                    "reasoning": ["scene_plan_failed"],
                }
            content = resp.data if isinstance(resp.data, str) else str(resp.data)
            parsed = extract_json_block(content)
            if not parsed:
                return {"error": "scene_plan_invalid_json", "raw": content}
            scenes = parsed.get("scenes") if isinstance(parsed, dict) else None
            if not scenes:
                return {"error": "scene_plan_empty", "raw": parsed}
            return {
                "scenes": scenes,
                "reasoning": ["scene_plan_ok"],
                "provider": resp.provider,
                "model_used": resp.model,
            }

        async def write_dialogues(state: Dict[str, Any]) -> Dict[str, Any]:
            scenes = state.get("scenes") or []
            prompt = prompt_manager.render_prompt(
                PromptTemplate.SCRIPT_DIALOGUES.value,
                {
                    "episode": episode,
                    "story": story,
                    "scenes": scenes,
                    "dialogue_style": dialogue_style,
                    "language": language,
                    "format_type": format_type,
                },
            )

            # Append word count constraints if scene budgets are provided
            if scene_budgets:
                constraints_text = self._build_word_count_constraints(
                    scene_budgets, scenes
                )
                prompt = prompt + constraints_text
                self.logger.info(
                    "write_dialogues: Added word count constraints for %d scenes",
                    len(scene_budgets),
                )

            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema={
                    "name": "script_dialogues",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dialogues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "anyOf": [
                                                {"type": "integer"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "character": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "content": {"type": "string"},
                                        "emotion": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "action": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                    },
                                },
                            },
                            "stage_directions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "anyOf": [
                                                {"type": "integer"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "timing": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "content": {"type": "string"},
                                        "type": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                system_prompt="你是专业的剧本对白与舞台指示写手，请严格按 JSON 返回。",
            )
            if not resp.success:
                return {
                    "error": "dialogue_failed",
                    "reasoning": state.get("reasoning", []) + ["dialogue_failed"],
                }
            content = resp.data if isinstance(resp.data, str) else str(resp.data)
            parsed = extract_json_block(content)
            if not parsed:
                return {"error": "dialogue_invalid_json", "raw": content}
            dialogues = parsed.get("dialogues") if isinstance(parsed, dict) else None
            stage_dir = (
                parsed.get("stage_directions") if isinstance(parsed, dict) else None
            )
            if not dialogues:
                return {"error": "dialogue_empty", "raw": parsed}
            reasoning = state.get("reasoning", []) + ["dialogue_ok"]
            return {
                "scenes": scenes,
                "dialogues": dialogues,
                "stage_directions": stage_dir or [],
                "reasoning": reasoning,
                "provider": state.get("provider") or resp.provider,
                "model_used": state.get("model_used") or resp.model,
            }

        async def review_classification(state: Dict[str, Any]) -> Dict[str, Any]:
            """Review and fix misclassified dialogues/stage_directions."""
            dialogues = state.get("dialogues") or []
            stage_dir = state.get("stage_directions") or []
            scenes = state.get("scenes") or []

            # Extract character names from story for context
            characters = []
            if story.get("characters"):
                for char in story["characters"]:
                    if isinstance(char, dict):
                        characters.append(char.get("name", ""))
                    elif isinstance(char, str):
                        characters.append(char)

            prompt = prompt_manager.render_prompt(
                PromptTemplate.SCRIPT_REVIEW.value,
                {
                    "dialogues": dialogues,
                    "stage_directions": stage_dir,
                    "characters": characters,
                },
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=0.3,  # Low temperature for accurate review
                model=model,
                prefer_provider=prefer_provider,
                json_schema={
                    "name": "script_review",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dialogues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "anyOf": [
                                                {"type": "integer"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "character": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "content": {"type": "string"},
                                        "emotion": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                    },
                                },
                            },
                            "stage_directions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "scene_number": {
                                            "anyOf": [
                                                {"type": "integer"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "timing": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                        "content": {"type": "string"},
                                        "type": {
                                            "anyOf": [
                                                {"type": "string"},
                                                {"type": "null"},
                                            ]
                                        },
                                    },
                                },
                            },
                            "corrections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "original_type": {"type": "string"},
                                        "corrected_type": {"type": "string"},
                                        "content": {"type": "string"},
                                        "reason": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
                system_prompt="你是专业的剧本审核专家，请严格按 JSON 返回修正后的对白和舞台指示。",
            )
            if not resp.success:
                # If review fails, keep original data
                self.logger.warning("Review classification failed, keeping original")
                reasoning = state.get("reasoning", []) + ["review_skipped"]
                return {
                    **state,
                    "reasoning": reasoning,
                }

            content = resp.data if isinstance(resp.data, str) else str(resp.data)
            parsed = extract_json_block(content)
            if not parsed or not isinstance(parsed, dict):
                self.logger.warning("Review returned invalid JSON, keeping original")
                reasoning = state.get("reasoning", []) + ["review_invalid_json"]
                return {
                    **state,
                    "reasoning": reasoning,
                }

            reviewed_dialogues = parsed.get("dialogues") or dialogues
            reviewed_stage_dir = parsed.get("stage_directions") or stage_dir
            corrections = parsed.get("corrections") or []

            if corrections:
                self.logger.info(
                    f"Review made {len(corrections)} corrections: "
                    f"{[c.get('content', '')[:30] for c in corrections]}"
                )

            reasoning = state.get("reasoning", []) + [
                f"review_ok({len(corrections)} corrections)"
            ]
            return {
                "scenes": scenes,
                "dialogues": reviewed_dialogues,
                "stage_directions": reviewed_stage_dir,
                "reasoning": reasoning,
                "provider": state.get("provider"),
                "model_used": state.get("model_used"),
            }

        def assemble(state: Dict[str, Any]) -> Dict[str, Any]:
            scenes = state.get("scenes") or []
            dialogues = state.get("dialogues") or []
            stage_dir = state.get("stage_directions") or []
            payload = {
                "content": "",  # 由上层写入整合后的文本内容
                "scenes": scenes,
                "dialogues": dialogues,
                "stage_directions": stage_dir,
                "metadata": {
                    "total_scenes": len(scenes),
                    "total_dialogues": len(dialogues),
                    "estimated_duration": f"{episode.get('duration_minutes') or 0}min",
                },
            }
            try:
                ScriptModel.model_validate(payload)
            except Exception as exc:
                return {
                    "error": "assemble_invalid",
                    "reasoning": state.get("reasoning", []) + ["assemble_invalid"],
                    "payload": payload,
                    "exc": str(exc),
                }
            return {
                "content": payload,
                "generation_method": "langgraph_script",
                "provider_used": state.get("provider"),
                "model_used": state.get("model_used"),
                "reasoning": state.get("reasoning", []) + ["done"],
            }

        graph.add_node("scene_plan", plan_scenes)
        graph.add_node("dialogue", write_dialogues)
        graph.add_node("review", review_classification)
        graph.add_node("assemble", assemble)
        graph.add_edge("scene_plan", "dialogue")
        graph.add_edge("dialogue", "review")
        graph.add_edge("review", "assemble")
        graph.add_edge("assemble", END)
        graph.set_entry_point("scene_plan")

        app = graph.compile()
        result = await app.ainvoke({})

        # Guard: if LangGraph failed to produce structured scenes + dialogues, treat as failure
        content = result.get("content") if isinstance(result, dict) else None
        if not content or not isinstance(content, dict):
            self.logger.warning("LangGraph script agent returned empty content")
            return None

        scenes = content.get("scenes") or []
        dialogues = content.get("dialogues") or []
        if not scenes or not dialogues:
            self.logger.warning(
                "LangGraph script agent missing scenes/dialogues, aborting to allow fallback",
            )
            return None

        return result
