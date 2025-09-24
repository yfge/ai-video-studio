from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.schemas.generation import StoryboardModel, StoryboardPlanModel, StoryboardPlanScene
from app.core.logging import get_logger

try:
    from langgraph.graph import StateGraph, END
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

        async def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan_resp = await self.service.generate_storyboard_plan(
                script=script,
                frames_per_scene=frames_per_scene,
                selected_scenes=selected_scenes,
                model=model,
                prefer_provider=prefer_provider,
                temperature=min(0.35, temperature),
            )
            if not plan_resp or not plan_resp.get("normalized"):
                return {"error": "plan_failed"}
            try:
                StoryboardPlanModel.model_validate(plan_resp["normalized"])
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph plan validation failed: {exc}")
                return {"error": "plan_invalid"}
            return {
                "plan": plan_resp["normalized"],
                "provider": plan_resp.get("provider_used"),
                "model_used": plan_resp.get("model_used"),
                "reasoning": state.get("reasoning", []) + ["plan_ready"],
            }

        def critique_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            duplicates: List[int] = []
            for scene in plan.get("scenes", []):
                combos = set()
                for frame in scene.get("frames", []):
                    key = (
                        frame.get("shot_type"),
                        frame.get("camera_movement"),
                        frame.get("intent"),
                    )
                    if key in combos:
                        duplicates.append(scene.get("scene_number"))
                        break
                    combos.add(key)
            if duplicates:
                self.logger.info(f"LangGraph critique: scenes {duplicates} contain repetitive outlines")
            return {"reasoning": state.get("reasoning", []) + ["plan_reviewed"]}

        async def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            frames_all: List[Dict[str, Any]] = []
            provider_used = state.get("provider")
            model_used = state.get("model_used")
            for scene in plan.get("scenes", []):
                try:
                    scene_plan = StoryboardPlanScene.model_validate(scene)
                except Exception:
                    continue
                frames_scene = await self.service.generate_storyboard_from_plan_for_scene(
                    script=script,
                    scene_plan=scene_plan,
                    model=model,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    max_frames=max_frames,
                )
                if frames_scene:
                    frames_all.extend(frames_scene)
            if not frames_all:
                return {"frames": [], "reasoning": state.get("reasoning", []) + ["frames_empty"]}
            try:
                StoryboardModel.model_validate({"frames": frames_all})
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph storyboard validation failed: {exc}")
                return {"frames": [], "error": "final_invalid"}
            return {
                "frames": frames_all,
                "provider": provider_used,
                "model_used": model_used,
                "reasoning": state.get("reasoning", []) + ["frames_ready"],
            }

        graph.add_node("plan", plan_node)
        graph.add_node("critique", critique_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "critique")
        graph.add_edge("critique", "finalize")
        graph.add_edge("finalize", END)

        app = graph.compile()
        result = await app.ainvoke({"reasoning": []})
        frames = result.get("frames")
        if not frames:
            return None
        content = json.dumps({"frames": frames}, ensure_ascii=False)
        return {
            "content": content,
            "generation_method": "langgraph_plan",
            "provider_used": result.get("provider"),
            "model_used": result.get("model_used"),
            "usage": None,
            "reasoning_trace": result.get("reasoning"),
        }


__all__ = ["StoryboardReActReasoner", "LANGGRAPH_AVAILABLE"]
