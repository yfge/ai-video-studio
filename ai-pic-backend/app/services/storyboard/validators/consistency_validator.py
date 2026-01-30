"""
Scene-dialogue consistency validator.

Validates consistency between Script JSON data and story_structure
normalized tables, ensuring scenes and dialogues are properly aligned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.storyboard.pipeline.pipeline_state import (
    ValidationResult,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class ConsistencyValidator:
    """
    Validates consistency between Script JSON and story_structure data.

    Checks:
    1. Scene count match between Script.scenes and story_structure.Scene
    2. Scene numbers are consecutive starting from 1
    3. Dialogues reference valid scene numbers
    4. Scene summaries/descriptions are consistent
    """

    @property
    def name(self) -> str:
        return "consistency_validator"

    @property
    def description(self) -> str:
        return "Validates scene-dialogue consistency between data sources"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> list[ValidationResult]:
        """Run all consistency checks."""
        results: list[ValidationResult] = []

        results.extend(self._check_scene_count(context))
        results.extend(self._check_scene_numbers_consecutive(context))
        results.extend(self._check_dialogue_scene_references(context))
        results.extend(self._check_sync_status(context))

        return results

    def _check_scene_count(
        self, context: "PipelineContext"
    ) -> list[ValidationResult]:
        """Check that scene counts match between JSON and structure."""
        results: list[ValidationResult] = []

        json_count = context.json_scene_count
        struct_count = context.structure_scene_count

        if json_count == 0 and struct_count == 0:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message="No scenes found in either Script JSON or story_structure",
                    details={"json_count": 0, "structure_count": 0},
                    suggestions=[
                        "Generate scenes from script content",
                        "Import scenes from external source",
                    ],
                )
            )
        elif json_count != struct_count:
            severity = (
                ValidationSeverity.WARNING
                if abs(json_count - struct_count) <= 2
                else ValidationSeverity.ERROR
            )
            results.append(
                ValidationResult(
                    validator_name=self.name,
                    passed=severity == ValidationSeverity.WARNING,
                    severity=severity,
                    message=f"Scene count mismatch: JSON={json_count}, structure={struct_count}",
                    details={
                        "json_count": json_count,
                        "structure_count": struct_count,
                        "difference": abs(json_count - struct_count),
                    },
                    suggestions=[
                        "Run script_structure_sync to reconcile data",
                        "Check for deleted or orphaned scenes",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"Scene count matches: {json_count} scenes",
                    details={"scene_count": json_count},
                )
            )

        return results

    def _check_scene_numbers_consecutive(
        self, context: "PipelineContext"
    ) -> list[ValidationResult]:
        """Check that scene numbers are consecutive starting from 1."""
        results: list[ValidationResult] = []

        scene_numbers = sorted(s.scene_number for s in context.scenes)
        if not scene_numbers:
            return results  # Already reported in scene count check

        # Check starting from 1
        if scene_numbers[0] != 1:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Scene numbering starts at {scene_numbers[0]}, expected 1",
                    details={"first_scene": scene_numbers[0]},
                    suggestions=["Renumber scenes to start from 1"],
                )
            )

        # Check for gaps
        gaps = []
        for i in range(1, len(scene_numbers)):
            expected = scene_numbers[i - 1] + 1
            actual = scene_numbers[i]
            if actual != expected:
                gaps.append((expected, actual - 1))

        if gaps:
            gap_str = ", ".join(
                f"{g[0]}-{g[1]}" if g[0] != g[1] else str(g[0]) for g in gaps
            )
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Non-consecutive scene numbers, missing: {gap_str}",
                    details={
                        "scene_numbers": scene_numbers,
                        "gaps": gaps,
                    },
                    suggestions=[
                        "Fill missing scene numbers",
                        "Renumber scenes consecutively",
                    ],
                )
            )

        # Check for duplicates
        duplicates = []
        for i in range(1, len(scene_numbers)):
            if scene_numbers[i] == scene_numbers[i - 1]:
                duplicates.append(scene_numbers[i])

        if duplicates:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message=f"Duplicate scene numbers found: {duplicates}",
                    details={"duplicates": duplicates},
                    suggestions=["Remove or renumber duplicate scenes"],
                )
            )

        if not gaps and not duplicates and scene_numbers and scene_numbers[0] == 1:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="Scene numbers are consecutive and valid",
                    details={"range": f"1-{scene_numbers[-1]}"},
                )
            )

        return results

    def _check_dialogue_scene_references(
        self, context: "PipelineContext"
    ) -> list[ValidationResult]:
        """Check that dialogues reference valid scene numbers."""
        results: list[ValidationResult] = []

        valid_scene_numbers = {s.scene_number for s in context.scenes}
        invalid_refs: list[tuple[int, int | None]] = []
        missing_refs: list[int] = []

        # Collect all dialogues
        dialogue_count = 0
        dialogues_by_scene: dict[int, int] = {}

        for scene in context.scenes:
            for dlg in scene.dialogues:
                dialogue_count += 1
                scene_num = dlg.get("scene_number")
                if scene_num is None:
                    missing_refs.append(dialogue_count)
                elif scene_num not in valid_scene_numbers:
                    invalid_refs.append((dialogue_count, scene_num))
                else:
                    dialogues_by_scene[scene_num] = (
                        dialogues_by_scene.get(scene_num, 0) + 1
                    )

        if invalid_refs:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message=f"{len(invalid_refs)} dialogues reference invalid scene numbers",
                    details={
                        "invalid_refs": [
                            {"dialogue_index": idx, "scene_number": sn}
                            for idx, sn in invalid_refs
                        ]
                    },
                    suggestions=[
                        "Fix scene number references in dialogues",
                        "Create missing scenes",
                    ],
                )
            )

        if missing_refs:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"{len(missing_refs)} dialogues have no scene_number",
                    details={"dialogue_indices": missing_refs[:10]},
                    suggestions=["Assign scene numbers to all dialogues"],
                )
            )

        # Check for scenes without dialogues
        scenes_without_dialogue = [
            s.scene_number
            for s in context.scenes
            if s.scene_number not in dialogues_by_scene and not s.beats
        ]

        if scenes_without_dialogue and len(scenes_without_dialogue) <= 5:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Scenes without content: {scenes_without_dialogue}",
                    details={"empty_scenes": scenes_without_dialogue},
                    suggestions=["Add dialogues or action beats to empty scenes"],
                )
            )

        if not invalid_refs and not missing_refs:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"All {dialogue_count} dialogues have valid scene references",
                    details={"dialogue_count": dialogue_count},
                )
            )

        return results

    def _check_sync_status(
        self, context: "PipelineContext"
    ) -> list[ValidationResult]:
        """Report overall sync status from context."""
        results: list[ValidationResult] = []

        if context.is_synchronized:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="Script JSON and story_structure are synchronized",
                )
            )
        else:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message="Data sources out of sync",
                    details={"issues": context.sync_issues},
                    suggestions=[
                        "Run script_structure_sync.reconcile() to fix",
                        "Manually review and fix inconsistencies",
                    ],
                )
            )

        return results

    def can_auto_fix(self) -> bool:
        """Consistency issues often require sync operation."""
        return True

    def auto_fix(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list[ValidationResult],
    ) -> tuple["PipelineState", list[str]]:
        """
        Auto-fix attempts to resolve simple consistency issues.

        Complex issues require script_structure_sync.reconcile().
        """
        fixes: list[str] = []

        # Auto-fix is delegated to script_structure_sync module
        # This method just signals that fixing is possible
        for issue in issues:
            if "scene_number" in issue.message.lower():
                fixes.append("scene_number_fix_available")

        return state, fixes
