"""
Pipeline context builder for storyboard generation.

Merges Script JSON data with normalized story_structure tables
to provide a unified context for generation and validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.script import Episode, Script
    from app.models.story_structure import Scene, SceneBeat


@dataclass
class SceneContext:
    """Unified scene context merging Script JSON and story_structure."""

    scene_number: int
    scene_id: int | None = None

    # From Script JSON
    location: str | None = None
    time: str | None = None
    description: str | None = None
    characters: list[str] = field(default_factory=list)

    # From story_structure Scene
    slug_line: str | None = None
    environment_type: str | None = None
    summary: str | None = None
    environment_id: int | None = None
    estimated_duration_seconds: int | None = None

    # Beats from story_structure
    beats: list[dict[str, Any]] = field(default_factory=list)

    # Dialogues from Script JSON for this scene
    dialogues: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PipelineContext:
    """
    Unified context for storyboard generation pipeline.

    Combines data from:
    - Script.scenes/dialogues JSON
    - story_structure.Scene/SceneBeat tables
    - Episode metadata
    """

    script_id: int
    episode_id: int | None = None

    # Script-level data
    script_content: str | None = None
    script_metadata: dict[str, Any] = field(default_factory=dict)

    # Unified scenes
    scenes: list[SceneContext] = field(default_factory=list)

    # Character info
    characters: list[dict[str, Any]] = field(default_factory=list)
    character_map: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Audio timeline (if available)
    audio_timeline: dict[str, Any] | None = None

    # Existing storyboard (if any)
    existing_storyboard: dict[str, Any] | None = None

    # Data sync status
    json_scene_count: int = 0
    structure_scene_count: int = 0
    is_synchronized: bool = False
    sync_issues: list[str] = field(default_factory=list)

    def get_scene(self, scene_number: int) -> SceneContext | None:
        """Get scene by scene number."""
        for scene in self.scenes:
            if scene.scene_number == scene_number:
                return scene
        return None

    def get_character(self, name: str) -> dict[str, Any] | None:
        """Get character info by name."""
        return self.character_map.get(name)

    def get_total_duration_seconds(self) -> int:
        """Calculate total estimated duration from scenes."""
        total = 0
        for scene in self.scenes:
            if scene.estimated_duration_seconds:
                total += scene.estimated_duration_seconds
        return total


def build_pipeline_context(
    db: "Session",
    *,
    script: "Script",
    episode: "Episode | None" = None,
    scenes: Sequence["Scene"] | None = None,
    beats_by_scene: dict[int, Sequence["SceneBeat"]] | None = None,
) -> PipelineContext:
    """
    Build unified pipeline context from Script and story_structure data.

    Args:
        db: Database session
        script: Script model instance
        episode: Optional Episode model instance
        scenes: Optional list of Scene models (loaded if not provided)
        beats_by_scene: Optional dict of scene_id -> SceneBeat list

    Returns:
        PipelineContext with merged data
    """
    from app.models.story_structure import Scene as SceneModel
    from app.models.story_structure import SceneBeat as SceneBeatModel

    ctx = PipelineContext(
        script_id=script.id,
        episode_id=episode.id if episode else None,
    )

    # Extract Script JSON data
    script_data = _extract_script_json(script)
    ctx.script_content = script_data.get("content")
    ctx.script_metadata = script_data.get("metadata", {})
    json_scenes = script_data.get("scenes", [])
    json_dialogues = script_data.get("dialogues", [])
    ctx.json_scene_count = len(json_scenes)

    # Load story_structure Scenes if not provided
    if scenes is None:
        scenes = (
            db.query(SceneModel)
            .filter(
                SceneModel.script_id == script.id,
                SceneModel.is_deleted.is_(False),
            )
            .order_by(SceneModel.scene_number)
            .all()
        )
    ctx.structure_scene_count = len(scenes)

    # Load beats by scene if not provided
    if beats_by_scene is None and scenes:
        scene_ids = [s.id for s in scenes]
        all_beats = (
            db.query(SceneBeatModel)
            .filter(SceneBeatModel.scene_id.in_(scene_ids))
            .order_by(SceneBeatModel.order_index)
            .all()
        )
        beats_by_scene = {}
        for beat in all_beats:
            beats_by_scene.setdefault(beat.scene_id, []).append(beat)

    # Build scene map from story_structure
    structure_scene_map: dict[int, "Scene"] = {}
    for scene in scenes or []:
        try:
            scene_num = int(str(scene.scene_number).strip())
            structure_scene_map[scene_num] = scene
        except (ValueError, TypeError):
            continue

    # Build dialogue map by scene number
    dialogue_map: dict[int, list[dict[str, Any]]] = {}
    for dlg in json_dialogues:
        scene_num = dlg.get("scene_number")
        if scene_num is not None:
            dialogue_map.setdefault(scene_num, []).append(dlg)

    # Merge scenes from both sources
    all_scene_numbers = set()
    for scene in json_scenes:
        if scene.get("scene_number"):
            all_scene_numbers.add(scene["scene_number"])
    all_scene_numbers.update(structure_scene_map.keys())

    for scene_num in sorted(all_scene_numbers):
        scene_ctx = _build_scene_context(
            scene_number=scene_num,
            json_scene=_find_json_scene(json_scenes, scene_num),
            structure_scene=structure_scene_map.get(scene_num),
            beats=beats_by_scene.get(
                structure_scene_map[scene_num].id, []
            ) if scene_num in structure_scene_map else [],
            dialogues=dialogue_map.get(scene_num, []),
        )
        ctx.scenes.append(scene_ctx)

    # Check synchronization
    ctx.is_synchronized = _check_sync_status(ctx)

    # Load audio timeline if episode provided
    if episode:
        ep_meta = episode.extra_metadata or {}
        ctx.audio_timeline = ep_meta.get("audio_timeline")

    # Load existing storyboard
    script_extra = script.extra_metadata or {}
    ctx.existing_storyboard = script_extra.get("storyboard")

    return ctx


def _extract_script_json(script: "Script") -> dict[str, Any]:
    """Extract JSON data from Script model."""
    result: dict[str, Any] = {
        "content": script.content,
        "scenes": [],
        "dialogues": [],
        "metadata": {},
    }

    if isinstance(script.scenes, list):
        result["scenes"] = script.scenes
    if isinstance(script.dialogues, list):
        result["dialogues"] = script.dialogues
    if isinstance(script.extra_metadata, dict):
        result["metadata"] = script.extra_metadata

    return result


def _find_json_scene(
    json_scenes: list[dict[str, Any]], scene_number: int
) -> dict[str, Any] | None:
    """Find scene in JSON scenes list by scene number."""
    for scene in json_scenes:
        if scene.get("scene_number") == scene_number:
            return scene
    return None


def _build_scene_context(
    *,
    scene_number: int,
    json_scene: dict[str, Any] | None,
    structure_scene: "Scene | None",
    beats: Sequence["SceneBeat"],
    dialogues: list[dict[str, Any]],
) -> SceneContext:
    """Build unified SceneContext from multiple sources."""
    ctx = SceneContext(scene_number=scene_number)

    # From JSON scene
    if json_scene:
        ctx.location = json_scene.get("location")
        ctx.time = json_scene.get("time")
        ctx.description = json_scene.get("description")
        ctx.characters = json_scene.get("characters", [])

    # From story_structure Scene
    if structure_scene:
        ctx.scene_id = structure_scene.id
        ctx.slug_line = structure_scene.slug_line
        ctx.environment_type = structure_scene.environment_type
        ctx.summary = structure_scene.summary
        ctx.environment_id = structure_scene.environment_id
        ctx.estimated_duration_seconds = structure_scene.estimated_duration_seconds
        # Use structure location if JSON doesn't have it
        if not ctx.location:
            ctx.location = structure_scene.location
        if not ctx.time:
            ctx.time = structure_scene.time_of_day

    # Add beats
    for beat in beats:
        beat_dict = {
            "beat_id": beat.id,
            "order_index": beat.order_index,
            "beat_type": beat.beat_type,
            "beat_summary": beat.beat_summary,
            "dialogue_excerpt": beat.dialogue_excerpt,
            "duration_seconds": float(beat.duration_seconds) if beat.duration_seconds else None,
            "characters_involved": beat.characters_involved,
        }
        ctx.beats.append(beat_dict)

    # Add dialogues
    ctx.dialogues = dialogues

    return ctx


def _check_sync_status(ctx: PipelineContext) -> bool:
    """Check if Script JSON and story_structure are synchronized."""
    issues = []

    # Check scene count match
    if ctx.json_scene_count != ctx.structure_scene_count:
        issues.append(
            f"Scene count mismatch: JSON has {ctx.json_scene_count}, "
            f"structure has {ctx.structure_scene_count}"
        )

    # Check for scenes missing from either source
    json_scene_nums = {s.scene_number for s in ctx.scenes if s.location or s.description}
    struct_scene_nums = {s.scene_number for s in ctx.scenes if s.scene_id}

    json_only = json_scene_nums - struct_scene_nums
    struct_only = struct_scene_nums - json_scene_nums

    if json_only:
        issues.append(f"Scenes only in JSON: {sorted(json_only)}")
    if struct_only:
        issues.append(f"Scenes only in structure: {sorted(struct_only)}")

    ctx.sync_issues = issues
    return len(issues) == 0
