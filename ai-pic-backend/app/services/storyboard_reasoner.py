from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.schemas.generation import (
    StoryboardModel,
    StoryboardPlanModel,
    StoryboardPlanScene,
)
from app.services.storyboard.langgraph_utils import (
    compute_scene_scope,
    filter_plan_to_scope,
    find_scene_deficits,
    normalize_plan_outlines,
)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False
if TYPE_CHECKING:
    from .ai_service import AIService


class StoryboardReActReasoner:
    """Optional LangGraph-driven orchestrator for storyboard generation."""

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()

    async def generate(
        self,
        *,
        script: Dict[str, Any],
        frames_per_scene: int,
        max_frames: Optional[int],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
        selected_scenes: Optional[List[int]],
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None
        graph = StateGraph(dict)

        def select_node(state: Dict[str, Any]) -> Dict[str, Any]:
            reasoning = state.get("reasoning", []) + ["scenes_selected"]
            scope, error = compute_scene_scope(
                script, selected_scenes=selected_scenes
            )
            if error:
                return {
                    "error": error,
                    "reasoning": reasoning + [error],
                    "scene_scope": scope,
                }
            return {"scene_scope": scope, "reasoning": reasoning}

        async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
            scope = state.get("scene_scope")
            if not scope:
                return {
                    "error": "scene_scope_empty",
                    "reasoning": state.get("reasoning", [])
                    + ["scene_scope_empty"],
                }
            plan_resp = await self.service.generate_storyboard_plan(
                script=script,
                frames_per_scene=frames_per_scene,
                selected_scenes=scope,
                model=model,
                prefer_provider=prefer_provider,
                temperature=min(0.35, temperature),
            )
            if not plan_resp or not plan_resp.get("normalized"):
                return {
                    "error": "plan_failed",
                    "reasoning": state.get("reasoning", []) + ["plan_failed"],
                }
            try:
                StoryboardPlanModel.model_validate(plan_resp["normalized"])
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph plan validation failed: {exc}")
                return {
                    "error": "plan_invalid",
                    "reasoning": state.get("reasoning", []) + ["plan_invalid"],
                }
            reasoning = state.get("reasoning", []) + ["plan_ready"]
            return {
                "plan": plan_resp["normalized"],
                "provider": plan_resp.get("provider_used"),
                "model_used": plan_resp.get("model_used"),
                "usage": plan_resp.get("usage"),
                "reasoning": reasoning,
                "scene_scope": scope,
            }

        def critique_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            plan, fixes = normalize_plan_outlines(plan)
            filter_plan_to_scope(plan, state.get("scene_scope") or [])
            if fixes:
                self.logger.info("LangGraph critique applied: %s", "; ".join(fixes))
            reasoning = state.get("reasoning", []) + ["plan_reviewed"]
            return {"plan": plan, "reasoning": reasoning, "fixes": fixes}

        async def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            frames_all: List[Dict[str, Any]] = []
            provider_used = state.get("provider")
            model_used = state.get("model_used")
            per_scene_logs: List[str] = []
            for scene in plan.get("scenes", []):
                try:
                    scene_plan = StoryboardPlanScene.model_validate(scene)
                except Exception:
                    continue
                target_frames = scene_plan.target_frames or frames_per_scene
                frames_scene = (
                    await self.service.generate_storyboard_from_plan_for_scene(
                        script=script,
                        scene_plan=scene_plan,
                        model=model,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        max_frames=max_frames,
                    )
                )
                if frames_scene:
                    frames_all.extend(frames_scene)
                    per_scene_logs.append(
                        f"scene {scene_plan.scene_number}: {len(frames_scene)}/{target_frames}"
                    )
            if per_scene_logs:
                self.logger.info(
                    "LangGraph generated storyboard frames: %s",
                    "; ".join(per_scene_logs),
                )
            reasoning = state.get("reasoning", []) + ["frames_generated"]
            return {
                "frames": frames_all,
                "provider": provider_used,
                "model_used": model_used,
                "reasoning": reasoning,
                "plan": plan,
            }

        def validate_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            frames = state.get("frames") or []
            deficits = find_scene_deficits(plan, frames, frames_per_scene)
            errors: List[str] = []
            if not frames:
                errors.append("frames_empty")
            try:
                StoryboardModel.model_validate({"frames": frames})
            except Exception:  # pragma: no cover - schema guard
                errors.append("frames_invalid")
            if deficits:
                errors.append("frames_insufficient")
            reasoning = state.get("reasoning", []) + (errors or ["frames_valid"])
            repair_round = int(state.get("repair_round") or 0)
            needs_repair = bool(errors) and repair_round < 1
            return {
                "frames": frames,
                "plan": plan,
                "deficits": deficits,
                "frames_invalid": "frames_invalid" in errors,
                "needs_repair": needs_repair,
                "reasoning": reasoning,
                "repair_round": repair_round,
            }

        async def repair_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            deficits = state.get("deficits") or {}
            frames = list(state.get("frames") or [])
            if state.get("frames_invalid"):
                frames = []
            for scene in plan.get("scenes", []):
                scene_no = scene.get("scene_number")
                missing = deficits.get(scene_no, 0)
                if missing <= 0:
                    continue
                try:
                    scene_plan = StoryboardPlanScene.model_validate(scene)
                except Exception:
                    continue
                extra_frames = (
                    await self.service.generate_storyboard_from_plan_for_scene(
                        script=script,
                        scene_plan=scene_plan,
                        model=model,
                        prefer_provider=prefer_provider,
                        temperature=temperature,
                        max_frames=max_frames,
                    )
                )
                if extra_frames:
                    frames.extend(extra_frames[:missing])
            reasoning = state.get("reasoning", []) + ["frames_repaired"]
            return {
                "frames": frames,
                "plan": plan,
                "reasoning": reasoning,
                "repair_round": int(state.get("repair_round") or 0) + 1,
            }

        def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
            frames = state.get("frames") or []
            plan = state.get("plan") or {}
            if not frames:
                reasoning = state.get("reasoning", []) + ["frames_empty"]
                return {"error": "frames_empty", "reasoning": reasoning}
            try:
                StoryboardModel.model_validate({"frames": frames})
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph storyboard validation failed: {exc}")
                reasoning = state.get("reasoning", []) + ["frames_invalid"]
                return {"error": "frames_invalid", "reasoning": reasoning}
            reasoning = state.get("reasoning", []) + ["frames_ready"]
            return {
                "frames": frames,
                "provider": state.get("provider"),
                "model_used": state.get("model_used"),
                "reasoning": reasoning,
                "plan": plan,
                "fixes": state.get("fixes"),
                "usage": state.get("usage"),
                "scene_scope": state.get("scene_scope"),
            }

        graph.add_node("select", select_node)
        graph.add_node("plan", plan_node)
        graph.add_node("critique", critique_node)
        graph.add_node("generate", generate_node)
        graph.add_node("validate", validate_node)
        graph.add_node("repair", repair_node)
        graph.add_node("finalize", finalize_node)
        graph.set_entry_point("select")

        def _route_after_select(state: Dict[str, Any]) -> str:
            return END if state.get("error") else "plan"

        def _route_after_plan(state: Dict[str, Any]) -> str:
            return END if state.get("error") else "critique"

        graph.add_conditional_edges("select", _route_after_select)
        graph.add_conditional_edges("plan", _route_after_plan)
        graph.add_edge("critique", "generate")
        graph.add_edge("generate", "validate")

        def _route_validate(state: Dict[str, Any]) -> str:
            return "repair" if state.get("needs_repair") else "finalize"

        graph.add_conditional_edges("validate", _route_validate)
        graph.add_edge("repair", "validate")
        graph.add_edge("finalize", END)
        app = graph.compile()
        result = await app.ainvoke({"reasoning": []})
        frames = result.get("frames")
        if result.get("error") or frames is None:
            return None
        frames = frames or []
        if not frames:
            return None
        content = json.dumps({"frames": frames}, ensure_ascii=False)
        return {
            "content": content,
            "generation_method": "langgraph_plan",
            "provider_used": result.get("provider"),
            "model_used": result.get("model_used"),
            "usage": result.get("usage"),
            "reasoning_trace": result.get("reasoning"),
            "plan": result.get("plan"),
            "fixes": result.get("fixes"),
            "scene_scope": result.get("scene_scope"),
        }


__all__ = ["StoryboardReActReasoner", "LANGGRAPH_AVAILABLE"]
