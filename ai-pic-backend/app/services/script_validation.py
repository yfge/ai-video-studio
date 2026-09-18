"""Script validation orchestration extracted from the legacy ScriptLangGraphAgent.

This module owns post-generation validation only. It deliberately does not own
LangGraph orchestration or script generation so those responsibilities can evolve
independently.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.validators.character_registry import normalize_generic_role
from app.repositories.script_lookup_repository import fetch_episode_character_sources
from app.services.validators.character_consistency_validator import CharacterConsistencyValidator, CharacterProfile
from app.services.validators.info_gate_validator import InfoGateValidator
from app.services.validators.scene_transition_validator import SceneTransitionValidator
from app.services.validators.script_quality_validator import ScriptQualityValidator

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ScriptValidationSuite:
    """Focused validation boundary for generated script content."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger
        self._character_validator = CharacterConsistencyValidator()
        self._quality_validator = ScriptQualityValidator()

    def build_character_profiles(
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


    def validate_script_characters(
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
            "unknown_names": [],
        }

        # Build profiles from story characters
        profiles = self.build_character_profiles(story_characters)

        # Add Episode temporary characters if available
        if episode_id and db:
            try:
                for ec, vip in fetch_episode_character_sources(db, episode_id):
                    if not vip:
                        continue
                    char_name = ec.character_name or vip.name
                    if not char_name:
                        continue
                    char_dict = {
                        "character_name": char_name,
                        "personality": ec.personality or vip.background_story or "",
                        "background": ec.background or vip.biography or "",
                        "role_type": ec.role_type or "temporary",
                    }
                    profiles.extend(self.build_character_profiles([char_dict]))
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
                and not normalize_generic_role(s)
            }

        if unknown_speakers:
            results["unknown_names"] = sorted(unknown_speakers)
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


    def validate_info_gate(
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


    def validate_scene_transitions(
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


    def validate_script_quality(
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

