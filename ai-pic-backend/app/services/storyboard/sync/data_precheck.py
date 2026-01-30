"""
Pre-generation data validation.

Validates that all required data is available before starting
storyboard generation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.script import Episode, Script
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext


@dataclass
class PrecheckResult:
    """Result of pre-generation validation."""

    ready: bool
    message: str
    checks: dict[str, bool] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ready": self.ready,
            "message": self.message,
            "checks": self.checks,
            "warnings": self.warnings,
            "errors": self.errors,
            "suggestions": self.suggestions,
        }


class DataPrecheck:
    """
    Pre-generation validation for storyboard pipeline.

    Validates:
    1. Script exists and has content
    2. Episode has audio timeline (if episode-based generation)
    3. Scenes exist and are valid
    4. Required metadata is present
    """

    def __init__(self, db: "Session"):
        self.db = db

    def check(
        self,
        *,
        script: "Script",
        episode: "Episode | None" = None,
        require_audio_timeline: bool = False,
    ) -> PrecheckResult:
        """
        Run all pre-generation checks.

        Args:
            script: Script model instance
            episode: Optional Episode for audio-timeline-based generation
            require_audio_timeline: Whether audio timeline is required
        """
        result = PrecheckResult(ready=True, message="")

        # Check script
        self._check_script(script, result)

        # Check episode and audio timeline
        if episode:
            self._check_episode(episode, script, result)
            if require_audio_timeline:
                self._check_audio_timeline(episode, script, result)

        # Check scenes
        self._check_scenes(script, result)

        # Determine overall readiness
        result.ready = len(result.errors) == 0

        if result.ready:
            result.message = "All pre-checks passed"
        else:
            result.message = f"Pre-check failed: {len(result.errors)} errors"

        return result

    def check_from_context(
        self,
        context: "PipelineContext",
    ) -> PrecheckResult:
        """Run pre-checks using pipeline context."""
        result = PrecheckResult(ready=True, message="")

        # Check scene data
        if not context.scenes:
            result.errors.append("No scenes found in context")
            result.suggestions.append("Generate scenes from script content first")
            result.checks["has_scenes"] = False
        else:
            result.checks["has_scenes"] = True

            # Check scene content
            empty_scenes = [
                s.scene_number
                for s in context.scenes
                if not s.description and not s.summary and not s.beats
            ]
            if empty_scenes:
                result.warnings.append(
                    f"Empty scenes without content: {empty_scenes[:5]}"
                )

        # Check sync status
        result.checks["is_synchronized"] = context.is_synchronized
        if not context.is_synchronized:
            result.warnings.append("Data sources not synchronized")
            result.suggestions.append("Run script_structure_sync to reconcile")

        # Check audio timeline if present
        if context.audio_timeline:
            result.checks["has_audio_timeline"] = True
            beats = context.audio_timeline.get("beats")
            if not isinstance(beats, list) or not beats:
                result.errors.append("Audio timeline has no beats")
                result.checks["audio_timeline_valid"] = False
            else:
                result.checks["audio_timeline_valid"] = True
        else:
            result.checks["has_audio_timeline"] = False

        result.ready = len(result.errors) == 0
        result.message = (
            "Pre-checks passed" if result.ready else f"{len(result.errors)} errors"
        )
        return result

    def _check_script(self, script: "Script", result: PrecheckResult) -> None:
        """Check script validity."""
        if not script:
            result.errors.append("Script not found")
            result.checks["script_exists"] = False
            return

        result.checks["script_exists"] = True

        # Check content
        if not script.content:
            result.warnings.append("Script has no content")
            result.checks["has_content"] = False
        else:
            result.checks["has_content"] = True

        # Check JSON data
        if isinstance(script.scenes, list) and script.scenes:
            result.checks["has_json_scenes"] = True
        else:
            result.checks["has_json_scenes"] = False
            result.warnings.append("Script has no JSON scenes")

        if isinstance(script.dialogues, list) and script.dialogues:
            result.checks["has_json_dialogues"] = True
        else:
            result.checks["has_json_dialogues"] = False
            result.warnings.append("Script has no JSON dialogues")

    def _check_episode(
        self,
        episode: "Episode",
        script: "Script",
        result: PrecheckResult,
    ) -> None:
        """Check episode validity."""
        if not episode:
            return

        result.checks["episode_exists"] = True

        # Check episode-script relationship
        if episode.script_id != script.id:
            result.errors.append(
                f"Episode script_id ({episode.script_id}) doesn't match "
                f"script ({script.id})"
            )
            result.checks["episode_script_match"] = False
        else:
            result.checks["episode_script_match"] = True

    def _check_audio_timeline(
        self,
        episode: "Episode",
        script: "Script",
        result: PrecheckResult,
    ) -> None:
        """Check audio timeline availability and validity."""
        ep_meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
        audio_timeline = ep_meta.get("audio_timeline")

        if not isinstance(audio_timeline, dict):
            result.errors.append("Episode has no audio_timeline")
            result.checks["has_audio_timeline"] = False
            result.suggestions.append("Generate audio timeline first")
            return

        result.checks["has_audio_timeline"] = True

        # Check script_id match
        timeline_script_id = audio_timeline.get("script_id")
        if timeline_script_id != script.id:
            result.errors.append(
                f"Audio timeline script_id ({timeline_script_id}) doesn't match "
                f"script ({script.id})"
            )
            result.checks["audio_timeline_script_match"] = False
        else:
            result.checks["audio_timeline_script_match"] = True

        # Check beats
        beats = audio_timeline.get("beats")
        if not isinstance(beats, list):
            result.errors.append("Audio timeline has no beats array")
            result.checks["audio_timeline_has_beats"] = False
        elif not beats:
            result.errors.append("Audio timeline beats array is empty")
            result.checks["audio_timeline_has_beats"] = False
        else:
            result.checks["audio_timeline_has_beats"] = True

            # Check beat structure
            valid_beats = 0
            for beat in beats:
                if isinstance(beat, dict):
                    if beat.get("start_ms") is not None and beat.get("end_ms") is not None:
                        valid_beats += 1

            if valid_beats == 0:
                result.errors.append("No beats have valid start_ms/end_ms")
            elif valid_beats < len(beats):
                result.warnings.append(
                    f"Only {valid_beats}/{len(beats)} beats have valid time data"
                )

    def _check_scenes(self, script: "Script", result: PrecheckResult) -> None:
        """Check scene availability from story_structure."""
        from app.models.story_structure import Scene as SceneModel

        scene_count = (
            self.db.query(SceneModel)
            .filter(
                SceneModel.script_id == script.id,
                SceneModel.is_deleted.is_(False),
            )
            .count()
        )

        if scene_count == 0:
            result.warnings.append("No scenes in story_structure")
            result.checks["has_structure_scenes"] = False

            # Check if JSON has scenes
            if result.checks.get("has_json_scenes"):
                result.suggestions.append(
                    "Run json_to_structure sync to create scenes"
                )
        else:
            result.checks["has_structure_scenes"] = True
            result.checks["structure_scene_count"] = scene_count
