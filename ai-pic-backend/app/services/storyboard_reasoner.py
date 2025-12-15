from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.generation import (
    StoryboardModel,
    StoryboardPlanModel,
    StoryboardPlanScene,
)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


SHOT_CYCLE = ["远景", "中景", "近景", "特写"]
MOVEMENT_CYCLE = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
COMPOSITION_CYCLE = ["三分法", "对称", "前后景", "对角线", "中心对称"]


def _cycle_value(cycle: List[str], position: int) -> str:
    if not cycle:
        return ""
    return cycle[position % len(cycle)]


def _sanitize_outline(
    scene_number: int | None, index: int, outline: Dict[str, Any]
) -> Tuple[Dict[str, Any], bool]:
    changed = False
    shot = outline.get("shot_type")
    movement = outline.get("camera_movement")
    composition = outline.get("composition")
    if not shot:
        shot = _cycle_value(SHOT_CYCLE, index + (scene_number or 0))
        outline["shot_type"] = shot
        changed = True
    if not movement:
        movement = _cycle_value(MOVEMENT_CYCLE, index)
        outline["camera_movement"] = movement
        changed = True
    if not composition:
        composition = _cycle_value(COMPOSITION_CYCLE, index)
        outline["composition"] = composition
        changed = True
    if not outline.get("intent"):
        outline["intent"] = f"强调{movement}镜头表现" if movement else "突出叙事节奏"
        changed = True
    return outline, changed


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
                "reasoning": reasoning,
            }

        def critique_node(state: Dict[str, Any]) -> Dict[str, Any]:
            plan = state.get("plan") or {}
            fixes: List[str] = []
            for scene in plan.get("scenes", []):
                outlines = scene.get("frames") or []
                combos = set()
                scene_no = scene.get("scene_number")
                for idx, frame in enumerate(outlines):
                    frame, changed = _sanitize_outline(scene_no, idx, frame)
                    key = (
                        frame.get("shot_type"),
                        frame.get("camera_movement"),
                        frame.get("intent"),
                    )
                    if key in combos:
                        shot = _cycle_value(SHOT_CYCLE, idx + 1)
                        move = _cycle_value(MOVEMENT_CYCLE, idx + 2)
                        comp = _cycle_value(COMPOSITION_CYCLE, idx + 3)
                        frame["shot_type"] = shot
                        frame["camera_movement"] = move
                        frame["composition"] = comp
                        frame["intent"] = frame.get("intent") or f"镜头强调{move}"
                        combos.add((shot, move, frame["intent"]))
                        fixes.append(f"scene {scene_no} frame {idx} varied")
                        continue
                    combos.add(key)
                    if changed:
                        fixes.append(f"scene {scene_no} frame {idx} normalized")
            if fixes:
                self.logger.info("LangGraph critique applied: %s", "; ".join(fixes))
            reasoning = state.get("reasoning", []) + ["plan_reviewed"]
            return {"plan": plan, "reasoning": reasoning, "fixes": fixes}

        async def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
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
                # 允许最多两轮尝试，为“数量不足”场景做一次 ReAct 补救
                frames_scene_all: List[Dict[str, Any]] = []
                attempts = 0
                while attempts < 2 and len(frames_scene_all) < target_frames:
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
                    attempts += 1
                    if frames_scene:
                        frames_scene_all.extend(frames_scene)
                    if not frames_scene:
                        # 本轮完全失败，留给下一轮或后续 fallback 处理
                        break

                if frames_scene_all:
                    frames_all.extend(frames_scene_all)
                    per_scene_logs.append(
                        f"scene {scene_plan.scene_number}: {len(frames_scene_all)}/{target_frames} frames (attempts={attempts})"
                    )
                    # 如仍不足，只记录告警，后续由上层 fallback 做兜底
                    if len(frames_scene_all) < target_frames:
                        self.logger.warning(
                            "Storyboard frames insufficient after retries",
                            extra={
                                "scene_number": scene_plan.scene_number,
                                "target_frames": target_frames,
                                "generated": len(frames_scene_all),
                                "attempts": attempts,
                            },
                        )
                else:
                    self.logger.warning(
                        "Storyboard frames empty for scene after retries",
                        extra={
                            "scene_number": scene_plan.scene_number,
                            "attempts": attempts,
                        },
                    )

            if not frames_all:
                reasoning = state.get("reasoning", []) + ["frames_empty"]
                return {"frames": [], "reasoning": reasoning, "plan": plan}
            try:
                StoryboardModel.model_validate({"frames": frames_all})
            except Exception as exc:  # pragma: no cover - schema guard
                self.logger.warning(f"LangGraph storyboard validation failed: {exc}")
                reasoning = state.get("reasoning", []) + ["frames_invalid"]
                return {
                    "frames": [],
                    "error": "final_invalid",
                    "reasoning": reasoning,
                    "plan": plan,
                }
            if per_scene_logs:
                self.logger.info(
                    "LangGraph finalize produced frames: %s", "; ".join(per_scene_logs)
                )
            reasoning = state.get("reasoning", []) + ["frames_ready"]
            return {
                "frames": frames_all,
                "provider": provider_used,
                "model_used": model_used,
                "reasoning": reasoning,
                "plan": plan,
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
            "usage": None,
            "reasoning_trace": result.get("reasoning"),
            "plan": result.get("plan"),
            "fixes": result.get("fixes"),
        }


__all__ = ["StoryboardReActReasoner", "LANGGRAPH_AVAILABLE"]
