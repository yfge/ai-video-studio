"""Plan and frame-generation nodes for StoryboardPipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from app.schemas.generation import StoryboardPlanModel, StoryboardPlanScene
from app.services.storyboard.langgraph_utils import (
    filter_plan_to_scope,
    normalize_plan_outlines,
)
from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelinePhase,
    PipelineState,
    ValidationResult,
)

if TYPE_CHECKING:
    from app.models.script import Script


class StoryboardPipelinePlanMixin:
    """Plan generation and frame expansion nodes."""

    async def _generate_frames_via_service(
        self,
        state: PipelineState,
        context: PipelineContext,
        script: "Script",
    ) -> list[Dict[str, Any]]:
        """Generate frames using AIService direct fallback."""
        if not self.ai_service:
            return []

        result = await self.ai_service.generate_storyboard(
            script=self._build_script_payload(script),
            frames_per_scene=state.frames_per_scene,
            selected_scenes=state.selected_scenes,
            model=getattr(state, "model", None),
            prefer_provider=getattr(state, "prefer_provider", None),
            temperature=state.temperature,
            max_frames=getattr(state, "max_frames", None),
            prefer_graph=False,
        )
        if result and "frames" in result:
            return result["frames"]
        if result and isinstance(result.get("normalized"), dict):
            frames = result["normalized"].get("frames")
            if isinstance(frames, list):
                return frames
        if result and result.get("content"):
            import json

            try:
                parsed = json.loads(result["content"])
                return parsed.get("frames", [])
            except json.JSONDecodeError:
                pass
        return []

    def _build_script_payload(self, script: "Script") -> Dict[str, Any]:
        """Build the AIService script payload with stable JSON-safe defaults."""
        scenes = getattr(script, "scenes", None)
        scenes = scenes if isinstance(scenes, list) else []
        dialogues = getattr(script, "dialogues", None)
        dialogues = dialogues if isinstance(dialogues, list) else []
        stage_directions = getattr(script, "stage_directions", None)
        stage_directions = (
            stage_directions if isinstance(stage_directions, list) else []
        )
        extra_metadata = getattr(script, "extra_metadata", None)
        extra_metadata = extra_metadata if isinstance(extra_metadata, dict) else {}

        scene_indices: list[int] = []
        for fallback_index, scene in enumerate(scenes, start=1):
            scene_number = (
                scene.get("scene_number")
                if isinstance(scene, dict)
                else getattr(scene, "scene_number", None)
            )
            try:
                scene_indices.append(int(scene_number or fallback_index))
            except (TypeError, ValueError):
                scene_indices.append(fallback_index)

        payload: Dict[str, Any] = {
            "id": getattr(script, "id", None),
            "content": getattr(script, "content", "") or "",
            "scenes": scenes,
            "dialogues": dialogues,
            "stage_directions": stage_directions,
        }
        if scene_indices:
            payload["scene_indices"] = scene_indices
        for key in ("story", "episode"):
            if extra_metadata.get(key) is not None:
                payload[key] = extra_metadata[key]
        return payload

    async def _node_generate_plan(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an explicit storyboard plan before frame generation."""
        ps: PipelineState = state_dict["pipeline_state"]
        script = state_dict.get("script")
        ps.phase = PipelinePhase.GENERATE_PLAN
        ps.add_reasoning("plan_generation_started")

        if not self.ai_service or script is None:
            message = "AI service unavailable for storyboard plan"
            if script is None:
                message = "Script missing for storyboard plan generation"
            ps.add_validation(ValidationResult.critical("storyboard_plan", message))
            ps.add_reasoning("plan_failed")
            return state_dict

        plan_resp = await self.ai_service.generate_storyboard_plan(
            script=self._build_script_payload(script),
            frames_per_scene=ps.frames_per_scene,
            selected_scenes=ps.selected_scenes,
            model=getattr(ps, "model", None),
            prefer_provider=getattr(ps, "prefer_provider", None),
            temperature=min(0.35, ps.temperature),
        )
        plan_raw = plan_resp.get("normalized") if isinstance(plan_resp, dict) else None
        if not isinstance(plan_raw, dict):
            ps.add_validation(
                ValidationResult.critical(
                    "storyboard_plan",
                    "Storyboard plan generation returned no normalized plan",
                )
            )
            ps.add_reasoning("plan_failed")
            return state_dict

        try:
            StoryboardPlanModel.model_validate(plan_raw)
        except Exception as exc:
            ps.add_validation(
                ValidationResult.critical(
                    "storyboard_plan",
                    "Storyboard plan failed schema validation",
                    details={"error": str(exc)},
                )
            )
            ps.add_reasoning("plan_invalid")
            return state_dict

        plan, fixes = normalize_plan_outlines(dict(plan_raw))
        if ps.selected_scenes:
            plan = filter_plan_to_scope(plan, ps.selected_scenes)
        ps.plan = plan
        ps.provider_used = plan_resp.get("provider_used") or ps.provider_used
        ps.model_used = plan_resp.get("model_used") or ps.model_used
        ps.usage = plan_resp.get("usage") or ps.usage
        ps.add_reasoning("plan_generated")
        if fixes:
            ps.add_reasoning("plan_normalized")
        return state_dict

    def _node_validate_plan(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Plan validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        ps.phase = PipelinePhase.VALIDATE_PLAN
        if ps.plan is not None:
            try:
                plan_model = StoryboardPlanModel.model_validate(ps.plan)
            except Exception as exc:
                ps.add_validation(
                    ValidationResult.critical(
                        "storyboard_plan",
                        "Storyboard plan failed schema validation",
                        details={"error": str(exc)},
                    )
                )
                ps.add_reasoning("plan_invalid")
                return state_dict
            if not plan_model.scenes:
                ps.add_validation(
                    ValidationResult.critical(
                        "storyboard_plan",
                        "Storyboard plan has no scenes after scope filtering",
                    )
                )
                ps.add_reasoning("plan_empty")
                return state_dict
        else:
            ps.add_reasoning("plan_missing")

        for result in self.validators["consistency"].validate(ps, ctx):
            ps.add_validation(result)
        ps.add_reasoning("plan_validated")
        return state_dict

    async def _node_generate_frames(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Frame generation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        script = state_dict.get("script")
        ps.phase = PipelinePhase.GENERATE_FRAMES
        if self.ai_service and script and ps.plan:
            ps.frames = await self._generate_frames_from_plan(ps, script)
        elif self.ai_service and script:
            ps.frames = await self._generate_frames_via_service(ps, ctx, script)
        if not ps.frames:
            ps.add_validation(
                ValidationResult.error(
                    "storyboard_frames",
                    "Storyboard frame generation returned no frames",
                )
            )
        ps.add_reasoning(f"generated_{len(ps.frames)}_frames")
        return state_dict

    async def _generate_frames_from_plan(
        self,
        state: PipelineState,
        script: "Script",
    ) -> list[Dict[str, Any]]:
        """Generate storyboard frames from the explicit plan one scene at a time."""
        if not self.ai_service or not state.plan:
            return []
        frames_all: list[Dict[str, Any]] = []
        max_frames = getattr(state, "max_frames", None)
        for scene in state.plan.get("scenes", []) or []:
            if max_frames is not None and len(frames_all) >= max_frames:
                break
            try:
                scene_plan = StoryboardPlanScene.model_validate(scene)
            except Exception as exc:
                self.logger.warning(
                    "Skipping invalid storyboard plan scene during generation: %s", exc
                )
                continue
            remaining = max_frames - len(frames_all) if max_frames is not None else None
            frames_scene = (
                await self.ai_service.generate_storyboard_from_plan_for_scene(
                    script=self._build_script_payload(script),
                    scene_plan=scene_plan,
                    model=getattr(state, "model", None),
                    prefer_provider=getattr(state, "prefer_provider", None),
                    temperature=state.temperature,
                    max_frames=remaining,
                )
            )
            if frames_scene:
                frames_all.extend(frames_scene[:remaining])
        return frames_all
