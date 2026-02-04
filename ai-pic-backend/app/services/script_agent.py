from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.validators.script_dialogue_quality import (
    find_reused_short_dialogues,
    validate_scene_dialogues,
)
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import ScriptModel
from app.services.agent_core import FailureMode, FailurePatternMatcher, RepairMonitor
from app.services.duration_orchestrator.constants import (
    DIALOGUE_DENSITY_FACTOR,
    DURATION_TOLERANCE_SCENE_HIGH,
    DURATION_TOLERANCE_SCENE_LOW,
    MAX_RETRY_ATTEMPTS,
    MAX_SCENE_DURATION_SECONDS,
    MIN_SCENE_DURATION_SECONDS,
    WORDS_PER_SECOND,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.script_agent_react_fill import try_fill_pending_scenes_after_react
from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
)
from app.services.validators.info_gate_validator import InfoGateValidator
from app.services.validators.scene_transition_validator import SceneTransitionValidator
from app.services.validators.script_quality_validator import ScriptQualityValidator
from app.utils.json_utils import extract_json_block

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

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
        self._character_validator = CharacterConsistencyValidator()
        self._quality_validator = ScriptQualityValidator()
        # Monitoring infrastructure from Universal Agent Framework
        self._repair_monitor = RepairMonitor(slo_threshold=0.7, window_size=100)
        self._failure_matcher = FailurePatternMatcher()

    def _build_character_profiles(
        self, characters: List[Dict[str, Any]]
    ) -> List[CharacterProfile]:
        """Convert character dicts to CharacterProfile objects."""
        profiles = []
        for char in characters:
            if not char.get("name"):
                continue
            profile = CharacterProfile(
                name=char.get("name", ""),
                aliases=char.get("aliases", []),
                role_type=char.get("role_type") or char.get("role"),
                gender=char.get("gender"),
                age=char.get("age"),
                personality=char.get("personality", []),
                appearance=char.get("appearance") or char.get("description"),
            )
            profiles.append(profile)
        return profiles

    def _validate_script_characters(
        self,
        content: Dict[str, Any],
        story_characters: List[Dict[str, Any]],
        episode_id: Optional[int] = None,
        db: Optional["Session"] = None,
    ) -> Dict[str, Any]:
        """
        Validate that script dialogue characters are consistent with story and episode.

        Args:
            content: Script content dict with dialogues
            story_characters: List of story character dicts
            episode_id: Optional episode ID to include episode characters
            db: Optional database session to fetch episode characters

        Returns validation results dict with:
        - character_validation_passed: bool
        - character_validation_results: list of validation results
        - character_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "character_validation_passed": True,
            "character_validation_results": [],
            "character_warnings": [],
        }

        # Build profiles from story characters
        profiles = self._build_character_profiles(story_characters)

        # Add Episode temporary characters if available
        if episode_id and db:
            try:
                from app.models.episode_character import EpisodeCharacter
                from app.models.virtual_ip import VirtualIP

                episode_chars = (
                    db.query(EpisodeCharacter)
                    .filter(
                        EpisodeCharacter.episode_id == episode_id,
                        EpisodeCharacter.is_deleted == False,
                    )
                    .all()
                )

                # Fetch VirtualIPs for these characters
                if episode_chars:
                    vip_ids = {ec.virtual_ip_id for ec in episode_chars}
                    vips = db.query(VirtualIP).filter(VirtualIP.id.in_(vip_ids)).all()
                    vip_by_id = {vip.id: vip for vip in vips}

                    # Build profiles for episode characters
                    for ec in episode_chars:
                        vip = vip_by_id.get(ec.virtual_ip_id)
                        if not vip:
                            continue

                        # Use character_name from EpisodeCharacter, fallback to VirtualIP name
                        char_name = ec.character_name or vip.name
                        if not char_name:
                            continue

                        # Build character dict similar to story characters
                        char_dict = {
                            "character_name": char_name,
                            "personality": ec.personality or vip.background_story or "",
                            "background": ec.background or vip.biography or "",
                            "role_type": ec.role_type or "temporary",
                        }

                        # Build profile and add to validator
                        episode_profiles = self._build_character_profiles([char_dict])
                        profiles.extend(episode_profiles)
            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch episode characters: {e}",
                    exc_info=True,
                )

        if not profiles:
            results["character_warnings"].append(
                "No story characters to validate against"
            )
            return results

        self._character_validator = CharacterConsistencyValidator()
        self._character_validator.register_profiles(profiles)

        # Validate dialogues
        dialogues = content.get("dialogues", [])
        unknown_speakers: set[str] = set()

        for dlg in dialogues:
            if isinstance(dlg, dict):
                speaker = dlg.get("character")
                if not speaker:
                    continue

                # Check if speaker is known
                canonical = self._character_validator.resolve_name(speaker)
                if not canonical:
                    unknown_speakers.add(speaker)

        if unknown_speakers:
            # Filter out narrator
            unknown_speakers = {
                s
                for s in unknown_speakers
                if s not in CharacterConsistencyValidator.NARRATOR_NAMES
            }

        if unknown_speakers:
            results["character_warnings"].append(
                f"Unknown speaker(s) in dialogues: {', '.join(sorted(unknown_speakers))}"
            )
            results["character_validation_passed"] = False
            results["character_validation_results"].append(
                {
                    "passed": False,
                    "severity": "warning",
                    "message": f"Found {len(unknown_speakers)} unknown speaker(s) in dialogues",
                    "details": {"unknown_speakers": list(unknown_speakers)},
                }
            )
        else:
            results["character_validation_results"].append(
                {
                    "passed": True,
                    "severity": "info",
                    "message": "All dialogue speakers are valid characters",
                }
            )

        return results

    def _validate_info_gate(
        self,
        content: Dict[str, Any],
        episode_number: int,
        continuity_ledger: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate that dialogue doesn't reference unrevealed information.

        Args:
            content: Script content dict with dialogues
            episode_number: Current episode number
            continuity_ledger: Optional continuity ledger with revealed_info_timeline

        Returns:
            Validation results dict with:
            - info_gate_validation_passed: bool
            - info_gate_violations: list of violation dicts
            - info_gate_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "info_gate_validation_passed": True,
            "info_gate_violations": [],
            "info_gate_warnings": [],
        }

        # Skip if no continuity ledger or no revealed info
        if not continuity_ledger:
            results["info_gate_warnings"].append("No continuity ledger provided")
            return results

        revealed_info = continuity_ledger.get("revealed_info_timeline", [])
        if not revealed_info:
            results["info_gate_warnings"].append("No revealed info timeline in ledger")
            return results

        # Import here to avoid circular dependency
        from app.schemas.continuity import RevealedInfoItem

        # Convert dict items to RevealedInfoItem objects
        revealed_items = []
        for item in revealed_info:
            if isinstance(item, dict):
                try:
                    revealed_items.append(RevealedInfoItem(**item))
                except Exception:
                    continue
            elif isinstance(item, RevealedInfoItem):
                revealed_items.append(item)

        if not revealed_items:
            return results

        # Create validator and register info
        validator = InfoGateValidator()
        validator.register_revealed_info(revealed_items)

        # Build script content structure for validation
        dialogues = content.get("dialogues", [])
        scenes = content.get("scenes", [])

        # Group dialogues by scene
        script_content = {"scenes": []}
        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            scene_dialogues = [
                d for d in dialogues if d.get("scene_number") == scene_num
            ]
            script_content["scenes"].append(
                {
                    "scene_number": scene_num,
                    "dialogues": scene_dialogues,
                }
            )

        # Run validation
        violations = validator.validate_script_content(script_content, episode_number)

        if violations:
            results["info_gate_validation_passed"] = False
            for v in violations:
                results["info_gate_violations"].append(v.to_dict())
                results["info_gate_warnings"].append(v.message)

            # Generate fix suggestions
            suggestions = validator.generate_fix_suggestions(violations)
            results["info_gate_fix_suggestions"] = suggestions

        return results

    def _validate_scene_transitions(
        self,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate physical plausibility of scene transitions.

        Args:
            content: Script content dict with scenes, dialogues, stage_directions

        Returns:
            Validation results dict with:
            - transition_validation_passed: bool
            - transition_issues: list of issue dicts
            - transition_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "transition_validation_passed": True,
            "transition_issues": [],
            "transition_warnings": [],
        }

        scenes = content.get("scenes", [])
        if len(scenes) < 2:
            return results  # Need at least 2 scenes

        # Build scene contents for validation
        dialogues = content.get("dialogues", [])
        stage_directions = content.get("stage_directions", [])

        scene_contents = []
        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            scene_dialogues = [
                d for d in dialogues if d.get("scene_number") == scene_num
            ]
            scene_stage_dirs = [
                sd for sd in stage_directions if sd.get("scene_number") == scene_num
            ]
            scene_contents.append(
                {
                    "dialogues": scene_dialogues,
                    "stage_directions": scene_stage_dirs,
                }
            )

        # Run validation
        validator = SceneTransitionValidator()
        issues = validator.validate_transitions(scenes, scene_contents)

        if issues:
            # Only fail on ERROR severity issues
            has_errors = any(i.severity.value == "error" for i in issues)
            results["transition_validation_passed"] = not has_errors

            for issue in issues:
                results["transition_issues"].append(issue.to_dict())
                results["transition_warnings"].append(issue.message)

            # Generate fix suggestions
            suggestions = validator.generate_fix_suggestions(issues)
            results["transition_fix_suggestions"] = suggestions

        return results

    def _validate_script_quality(
        self,
        content: Dict[str, Any],
        story_characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate script quality including dialogue authenticity and narrative techniques.

        Args:
            content: Script content dict with scenes, dialogues, stage_directions
            story_characters: List of character definitions

        Returns:
            Validation results dict with:
            - script_quality_passed: bool
            - script_quality_result: dict with scores and analysis
            - script_quality_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "script_quality_passed": True,
            "script_quality_result": {},
            "script_quality_warnings": [],
        }

        quality_result = self._quality_validator.validate(content, story_characters)

        results["script_quality_passed"] = quality_result.passed
        results["script_quality_result"] = quality_result.to_dict()

        for issue in quality_result.issues:
            if issue.severity.value in ("error", "warning"):
                results["script_quality_warnings"].append(issue.message)

        return results

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

    def _compute_budgets_from_scenes(
        self,
        scenes: List[Dict[str, Any]],
        duration_minutes: float,
    ) -> List[SceneBudget]:
        """Compute scene budgets from LLM-planned scenes with duration hints.

        If the LLM didn't assign estimated_duration_seconds, fall back to equal distribution.

        Args:
            scenes: List of scenes from scene_plan node, each may have:
                - estimated_duration_seconds (int): LLM-assigned duration
            duration_minutes: Total episode duration in minutes.

        Returns:
            List of SceneBudget objects with computed word count targets.
        """
        if not scenes:
            return []

        total_seconds = int(duration_minutes * 60)
        budgets: List[SceneBudget] = []

        # Check if LLM assigned durations
        llm_assigned = all(
            isinstance(s.get("estimated_duration_seconds"), (int, float))
            for s in scenes
        )

        if llm_assigned:
            # Use LLM-assigned durations, normalize to fit total
            raw_durations = [
                float(s.get("estimated_duration_seconds", 30)) for s in scenes
            ]
            raw_total = sum(raw_durations)
            if raw_total > 0:
                scale = total_seconds / raw_total
                normalized = [int(d * scale) for d in raw_durations]
            else:
                normalized = [total_seconds // len(scenes)] * len(scenes)
        else:
            # Equal distribution fallback
            per_scene = total_seconds // len(scenes) if scenes else 30
            normalized = [per_scene] * len(scenes)

        for idx, scene in enumerate(scenes):
            target_seconds = max(
                MIN_SCENE_DURATION_SECONDS,
                min(MAX_SCENE_DURATION_SECONDS, normalized[idx]),
            )

            # Compute word count: keep dialogue dense by default (short drama pacing)
            # to avoid under-filled scenes and timeline drift later.
            target_words = int(
                target_seconds * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND
            )

            budget = SceneBudget(
                scene_number=scene.get("scene_number", idx + 1),
                scene_index=idx,
                target_duration_seconds=target_seconds,
                target_word_count=target_words,
                min_duration_seconds=int(target_seconds * DURATION_TOLERANCE_SCENE_LOW),
                max_duration_seconds=int(
                    target_seconds * DURATION_TOLERANCE_SCENE_HIGH
                ),
                status=SceneStatus.PENDING,
                attempt_count=0,
            )
            budgets.append(budget)

        return budgets

    def _estimate_dialogue_duration(
        self,
        dialogues: List[Dict[str, Any]],
        scene_number: Optional[int] = None,
    ) -> float:
        """Estimate duration in seconds from dialogues.

        Args:
            dialogues: List of dialogue dicts with 'content' field.
            scene_number: If provided, filter to only this scene's dialogues.

        Returns:
            Estimated duration in seconds.
        """
        total_chars = 0
        for d in dialogues:
            if not isinstance(d, dict):
                continue
            if scene_number is not None:
                raw_scene_no = d.get("scene_number")
                try:
                    scene_no = int(raw_scene_no) if raw_scene_no is not None else None
                except (TypeError, ValueError):
                    scene_no = None
                if scene_no != scene_number:
                    continue
            content = d.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
        return total_chars / WORDS_PER_SECOND

    def _validate_scene_duration(
        self,
        budget: SceneBudget,
        actual_seconds: float,
    ) -> tuple[bool, str]:
        """Validate if actual duration is within tolerance.

        Args:
            budget: Scene budget with target duration.
            actual_seconds: Actual estimated duration.

        Returns:
            (is_valid, rejection_reason)
        """
        if actual_seconds < budget.min_duration_seconds:
            diff = budget.target_duration_seconds - actual_seconds
            extra_words = int(diff * WORDS_PER_SECOND)
            return (
                False,
                f"时长不足：实际 {actual_seconds:.1f}s < 目标 {budget.target_duration_seconds}s，需增加约 {extra_words} 字",
            )
        elif actual_seconds > budget.max_duration_seconds:
            diff = actual_seconds - budget.target_duration_seconds
            reduce_words = int(diff * WORDS_PER_SECOND)
            return (
                False,
                f"时长过长：实际 {actual_seconds:.1f}s > 目标 {budget.target_duration_seconds}s，需删减约 {reduce_words} 字",
            )
        return True, ""

    def _classify_failure_mode(self, error_text: str) -> FailureMode:
        """Classify validation error into a FailureMode.

        Uses FailurePatternMatcher for pattern-based classification,
        with fallback heuristics for script-specific errors.

        Args:
            error_text: The error message to classify.

        Returns:
            Classified FailureMode.
        """
        from app.services.agent_core.failure_patterns import PatternCategory

        # Category to mode mapping
        category_mapping = {
            PatternCategory.JSON_SYNTAX: FailureMode.JSON_PARSE,
            PatternCategory.SCHEMA_VIOLATION: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.MISSING_FIELD: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.CONTENT_LENGTH: FailureMode.CONTENT_CONSTRAINT,
            PatternCategory.CHARACTER_INCONSISTENCY: FailureMode.CHARACTER_INCONSISTENCY,
            PatternCategory.TIMELINE_ERROR: FailureMode.TIMELINE_ERROR,
            PatternCategory.LOGIC_ERROR: FailureMode.LOGIC_ERROR,
            PatternCategory.FORMAT_ERROR: FailureMode.SCHEMA_VIOLATION,
            PatternCategory.API_ERROR: FailureMode.API_ERROR,
        }

        # Try pattern-based classification first
        pattern = self._failure_matcher.match_first(error_text)
        if pattern:
            return category_mapping.get(pattern.category, FailureMode.UNKNOWN)

        # Script-specific heuristics for duration validation errors
        # These are common patterns in script agent that may not be in the
        # common failure patterns library
        error_lower = error_text.lower()

        # Duration constraints (most common in script agent REACT loop)
        if "时长" in error_lower or "duration" in error_lower:
            return FailureMode.CONTENT_CONSTRAINT

        # Dialogue quality issues
        if "对白" in error_lower or "dialogue" in error_lower:
            return FailureMode.CONTENT_CONSTRAINT

        # Repetition/reuse issues (logic errors)
        if (
            "重复" in error_lower
            or "reused" in error_lower
            or "repeated" in error_lower
        ):
            return FailureMode.LOGIC_ERROR

        # Character consistency
        if "角色" in error_lower or "character" in error_lower:
            return FailureMode.CHARACTER_INCONSISTENCY

        return FailureMode.UNKNOWN

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
        duration_minutes: Optional[float] = None,
        enable_react_validation: bool = True,
        continuity_ledger: Optional[Dict[str, Any]] = None,
        db: Optional["Session"] = None,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not self.service.ai_manager:
            return None

        # Extract duration_minutes from episode if not provided
        if duration_minutes is None:
            duration_minutes = episode.get("duration_minutes", 0) or 0

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
                    "duration_minutes": duration_minutes,
                    "min_scene_seconds": MIN_SCENE_DURATION_SECONDS,
                    "max_scene_seconds": MAX_SCENE_DURATION_SECONDS,
                },
            )
            # Build JSON schema - include duration fields if duration_minutes is set
            scene_properties: Dict[str, Any] = {
                "scene_number": {"type": "integer"},
                "slug_line": {"type": "string"},
                "location": {"type": "string"},
                "time_of_day": {"type": "string"},
                "summary": {"type": "string"},
            }
            if duration_minutes and duration_minutes > 0:
                scene_properties["estimated_duration_seconds"] = {"type": "integer"}
                scene_properties["dialogue_ratio"] = {"type": "number"}

            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=min(0.6, temperature),
                model=model,
                prefer_provider=prefer_provider,
                json_schema={
                    "name": "script_scenes",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "scenes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": scene_properties,
                                },
                            },
                        },
                    },
                },
                system_prompt="你是专业的剧本场景规划师，请严格按 JSON 返回。",
            )
            if not resp.success:
                return {
                    "error": "scene_plan_failed",
                    "reasoning": ["scene_plan_failed"],
                }
            parsed = (
                resp.data
                if isinstance(resp.data, dict)
                else extract_json_block(
                    resp.data if isinstance(resp.data, str) else str(resp.data)
                )
            )
            if not parsed:
                return {"error": "scene_plan_invalid_json", "raw": resp.data}
            scenes = parsed.get("scenes") if isinstance(parsed, dict) else None
            if not scenes:
                return {"error": "scene_plan_empty", "raw": parsed}

            # Compute scene budgets from LLM-planned scenes if duration control enabled
            computed_budgets: List[SceneBudget] = []
            if duration_minutes and duration_minutes > 0:
                computed_budgets = self._compute_budgets_from_scenes(
                    scenes, duration_minutes
                )
                self.logger.info(
                    "plan_scenes: Computed %d scene budgets from LLM-planned durations",
                    len(computed_budgets),
                )
                for b in computed_budgets:
                    self.logger.debug(
                        "  Scene %d: target=%ds, words=%d, dialogue_ratio=%.2f",
                        b.scene_number,
                        b.target_duration_seconds,
                        b.target_word_count,
                        scenes[b.scene_index].get(
                            "dialogue_ratio", DIALOGUE_DENSITY_FACTOR
                        ),
                    )

            return {
                "scenes": scenes,
                "computed_budgets": computed_budgets,
                "reasoning": ["scene_plan_ok"],
                "provider": resp.provider,
                "model_used": resp.model,
            }

        async def write_dialogues(state: Dict[str, Any]) -> Dict[str, Any]:
            scenes = state.get("scenes") or []
            # Use computed budgets from scene planning, or fall back to externally provided
            active_budgets = state.get("computed_budgets") or scene_budgets or []

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

            # Append word count constraints if scene budgets are available
            if active_budgets:
                constraints_text = self._build_word_count_constraints(
                    active_budgets, scenes
                )
                prompt = prompt + constraints_text
                self.logger.info(
                    "write_dialogues: Added word count constraints for %d scenes (source: %s)",
                    len(active_budgets),
                    "computed" if state.get("computed_budgets") else "external",
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
            parsed = (
                resp.data
                if isinstance(resp.data, dict)
                else extract_json_block(
                    resp.data if isinstance(resp.data, str) else str(resp.data)
                )
            )
            if not parsed:
                return {"error": "dialogue_invalid_json", "raw": resp.data}
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
                "computed_budgets": active_budgets,
                "reasoning": reasoning,
                "provider": state.get("provider") or resp.provider,
                "model_used": state.get("model_used") or resp.model,
            }

        async def react_validate_duration(state: Dict[str, Any]) -> Dict[str, Any]:
            """REACT validation: Check if dialogue durations match scene budgets.

            If any scene is outside tolerance and retry count < MAX_RETRY_ATTEMPTS,
            regenerate dialogues for that scene with adjustment hints.

            Also records repair attempts to RepairMonitor for observability.
            """
            validation_start = time.time()
            dialogues = state.get("dialogues") or []
            scenes = state.get("scenes") or []
            budgets = state.get("computed_budgets") or []
            reasoning = state.get("reasoning", [])

            if not budgets or not enable_react_validation:
                # No budgets or REACT disabled, skip validation
                return {**state, "reasoning": reasoning + ["react_skipped"]}

            reused_short_norms = find_reused_short_dialogues(dialogues)

            def _get_scene_dialogues(scene_num: int) -> list[dict[str, Any]]:
                matched: list[dict[str, Any]] = []
                for d in dialogues:
                    if not isinstance(d, dict):
                        continue
                    raw_scene_no = d.get("scene_number")
                    try:
                        scene_no = (
                            int(raw_scene_no) if raw_scene_no is not None else None
                        )
                    except (TypeError, ValueError):
                        scene_no = None
                    if scene_no == scene_num:
                        matched.append(d)
                return matched

            # Validate each scene's dialogue duration
            all_valid = True
            rejection_reasons = []
            updated_budgets = []

            for budget in budgets:
                scene_num = budget.scene_number
                scene_dialogues = _get_scene_dialogues(scene_num)
                estimated_seconds = self._estimate_dialogue_duration(
                    dialogues, scene_num
                )
                is_valid, reason = self._validate_scene_duration(
                    budget, estimated_seconds
                )

                issues = validate_scene_dialogues(
                    scene_dialogues,
                    min_lines=2,
                    repeated_short_norms=reused_short_norms,
                )
                if issues:
                    is_valid = False
                    issue_text = "；".join(i.message for i in issues)
                    reason = (
                        f"{reason}；{issue_text}".strip("；") if reason else issue_text
                    )

                if not is_valid:
                    all_valid = False
                    rejection_reasons.append(f"场景{scene_num}: {reason}")

                    # Update budget with rejection info for retry
                    updated_budget = SceneBudget(
                        scene_number=budget.scene_number,
                        scene_index=budget.scene_index,
                        target_duration_seconds=budget.target_duration_seconds,
                        target_word_count=budget.target_word_count,
                        min_duration_seconds=budget.min_duration_seconds,
                        max_duration_seconds=budget.max_duration_seconds,
                        status=SceneStatus.PENDING,
                        attempt_count=budget.attempt_count + 1,
                        adjustment_hint=reason,
                        actual_duration_seconds=estimated_seconds,
                    )
                    updated_budgets.append(updated_budget)
                else:
                    # Scene is valid, mark as committed
                    updated_budget = SceneBudget(
                        scene_number=budget.scene_number,
                        scene_index=budget.scene_index,
                        target_duration_seconds=budget.target_duration_seconds,
                        target_word_count=budget.target_word_count,
                        min_duration_seconds=budget.min_duration_seconds,
                        max_duration_seconds=budget.max_duration_seconds,
                        status=SceneStatus.COMMITTED,
                        attempt_count=budget.attempt_count,
                        actual_duration_seconds=estimated_seconds,
                    )
                    updated_budgets.append(updated_budget)

            # Calculate validation duration for monitoring
            validation_duration_ms = (time.time() - validation_start) * 1000

            if all_valid:
                self.logger.info("react_validate_duration: All scenes within tolerance")
                # Record successful validation (no repair needed)
                # Only record if this was a retry attempt (attempt_count > 0)
                for budget in updated_budgets:
                    if budget.attempt_count > 0:
                        self._repair_monitor.record(
                            failure_mode=FailureMode.CONTENT_CONSTRAINT,
                            strategy="duration_retry",
                            success=True,
                            duration_ms=validation_duration_ms,
                            error_before=budget.adjustment_hint
                            or "duration constraint",
                        )
                return {
                    **state,
                    "computed_budgets": updated_budgets,
                    "reasoning": reasoning + ["react_passed"],
                }

            # Check if any scene needs retry and hasn't exceeded max attempts
            needs_retry = any(
                b.status == SceneStatus.PENDING and b.attempt_count < MAX_RETRY_ATTEMPTS
                for b in updated_budgets
            )

            if needs_retry:
                self.logger.info(
                    "react_validate_duration: REACT rejection - %s",
                    "; ".join(rejection_reasons),
                )
                # Record failed validation attempt (will retry)
                for reason in rejection_reasons:
                    failure_mode = self._classify_failure_mode(reason)
                    self._repair_monitor.record(
                        failure_mode=failure_mode,
                        strategy="duration_retry",
                        success=False,
                        duration_ms=validation_duration_ms,
                        error_before=reason,
                    )
                return {
                    **state,
                    "computed_budgets": updated_budgets,
                    "react_needs_retry": True,
                    "reasoning": reasoning
                    + [f"react_rejected({'; '.join(rejection_reasons)})"],
                }
            else:
                # Max retries reached, accept as-is
                self.logger.warning(
                    "react_validate_duration: Max retries reached, accepting current result"
                )
                # Record final failure (max retries exceeded)
                for reason in rejection_reasons:
                    failure_mode = self._classify_failure_mode(reason)
                    self._repair_monitor.record(
                        failure_mode=failure_mode,
                        strategy="duration_retry_final",
                        success=False,
                        duration_ms=validation_duration_ms,
                        error_before=reason,
                        error_after="max_retries_exceeded",
                    )
                pending_budgets = [
                    b for b in updated_budgets if b.status == SceneStatus.PENDING
                ]
                if pending_budgets:
                    filled = await try_fill_pending_scenes_after_react(
                        ai_manager=self.service.ai_manager,
                        episode=episode,
                        story=story,
                        scenes=scenes,
                        pending_budgets=pending_budgets,
                        dialogue_style=dialogue_style,
                        language=language,
                        format_type=format_type,
                        temperature=temperature,
                        model=model,
                        prefer_provider=prefer_provider,
                        existing_dialogues=dialogues,
                        existing_stage_directions=state.get("stage_directions") or [],
                        build_word_count_constraints=self._build_word_count_constraints,
                    )
                    if filled:
                        merged_dialogues, merged_stage, pending_scene_numbers = filled
                        return {
                            **state,
                            "dialogues": merged_dialogues,
                            "stage_directions": merged_stage,
                            "computed_budgets": updated_budgets,
                            "reasoning": reasoning
                            + [
                                "react_max_retries_reached",
                                f"react_filled_pending_scenes({pending_scene_numbers})",
                            ],
                        }

                return {
                    **state,
                    "computed_budgets": updated_budgets,
                    "reasoning": reasoning + ["react_max_retries_reached"],
                }

        def should_retry_dialogues(state: Dict[str, Any]) -> str:
            """Conditional edge: decide whether to retry dialogue generation."""
            if state.get("react_needs_retry"):
                return "dialogue"  # Go back to dialogue generation
            return "review"  # Continue to review

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

            parsed = (
                resp.data
                if isinstance(resp.data, dict)
                else extract_json_block(
                    resp.data if isinstance(resp.data, str) else str(resp.data)
                )
            )
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
        graph.add_node("react_validate", react_validate_duration)
        graph.add_node("review", review_classification)
        graph.add_node("assemble", assemble)

        # Flow: scene_plan → dialogue → react_validate → (conditional) → review → assemble
        graph.add_edge("scene_plan", "dialogue")
        graph.add_edge("dialogue", "react_validate")
        graph.add_conditional_edges(
            "react_validate",
            should_retry_dialogues,
            {"dialogue": "dialogue", "review": "review"},
        )
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

        # Run character consistency validation
        story_characters = story.get("characters", [])
        char_validation = self._validate_script_characters(
            content, story_characters, episode.get("id"), db
        )
        if char_validation["character_warnings"]:
            self.logger.warning(
                "Script character validation warnings",
                extra={"warnings": char_validation["character_warnings"]},
            )

        # Run info gate validation (check for unrevealed information references)
        episode_number = episode.get("episode_number", 1)
        info_gate_validation = self._validate_info_gate(
            content, episode_number, continuity_ledger
        )
        if info_gate_validation["info_gate_warnings"]:
            self.logger.warning(
                "Script info gate validation warnings",
                extra={"warnings": info_gate_validation["info_gate_warnings"]},
            )

        # Run scene transition validation (check geographic/time/state plausibility)
        transition_validation = self._validate_scene_transitions(content)
        if transition_validation["transition_warnings"]:
            self.logger.warning(
                "Script scene transition validation warnings",
                extra={"warnings": transition_validation["transition_warnings"]},
            )

        # Run script quality validation (dialogue authenticity, show-don't-tell, etc.)
        quality_validation = self._validate_script_quality(content, story_characters)
        if quality_validation["script_quality_warnings"]:
            self.logger.warning(
                "Script quality validation warnings",
                extra={"warnings": quality_validation["script_quality_warnings"]},
            )

        # Merge validation results into result
        result.update(char_validation)
        result.update(info_gate_validation)
        result.update(transition_validation)
        result.update(quality_validation)

        # Add agent metrics from RepairMonitor for observability
        repair_metrics = self._repair_monitor.get_metrics()
        result["agent_metrics"] = {
            "repair_success_rate": repair_metrics.success_rate,
            "repair_attempts": repair_metrics.total_attempts,
            "successful_repairs": repair_metrics.successful_repairs,
            "attempts_by_mode": repair_metrics.to_dict().get("by_failure_mode", {}),
            "attempts_by_strategy": repair_metrics.to_dict().get("by_strategy", {}),
            "avg_repair_duration_ms": repair_metrics.avg_duration_ms,
            "problematic_patterns": self._repair_monitor.identify_problematic_patterns(),
        }

        return result
