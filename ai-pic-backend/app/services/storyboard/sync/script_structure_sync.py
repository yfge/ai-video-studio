"""
Script JSON <-> story_structure synchronization.

Reconciles data between Script.scenes/dialogues JSON fields
and normalized story_structure tables (Scene, SceneBeat).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.script import Script
    from app.models.story_structure import Scene, SceneBeat


@dataclass
class SyncResult:
    """Result of a synchronization operation."""

    success: bool
    message: str
    scenes_created: int = 0
    scenes_updated: int = 0
    beats_created: int = 0
    beats_updated: int = 0
    json_updated: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "scenes_created": self.scenes_created,
            "scenes_updated": self.scenes_updated,
            "beats_created": self.beats_created,
            "beats_updated": self.beats_updated,
            "json_updated": self.json_updated,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class ScriptStructureSync:
    """
    Synchronizes Script JSON with story_structure tables.

    Supports bidirectional sync:
    - json_to_structure: Creates/updates Scene/SceneBeat from Script JSON
    - structure_to_json: Updates Script JSON from Scene/SceneBeat tables
    - reconcile: Bidirectional merge preferring more complete data
    """

    def __init__(self, db: "Session"):
        self.db = db

    def json_to_structure(
        self,
        script: "Script",
        *,
        create_missing: bool = True,
        update_existing: bool = False,
    ) -> SyncResult:
        """
        Sync from Script JSON to story_structure tables.

        Args:
            script: Script model instance
            create_missing: Create Scene/SceneBeat for missing entries
            update_existing: Update existing Scene/SceneBeat from JSON
        """
        from app.models.story_structure import Scene as SceneModel
        from app.models.story_structure import SceneBeat as SceneBeatModel

        result = SyncResult(success=True, message="")

        # Extract JSON data
        json_scenes = script.scenes if isinstance(script.scenes, list) else []
        json_dialogues = script.dialogues if isinstance(script.dialogues, list) else []

        if not json_scenes:
            result.message = "No scenes in Script JSON"
            return result

        # Load existing scenes
        existing_scenes = (
            self.db.query(SceneModel)
            .filter(
                SceneModel.script_id == script.id,
                SceneModel.is_deleted.is_(False),
            )
            .all()
        )
        scene_map = {
            int(str(s.scene_number).strip()): s
            for s in existing_scenes
            if s.scene_number
        }

        # Build dialogue map
        dialogue_by_scene: dict[int, list[dict[str, Any]]] = {}
        for dlg in json_dialogues:
            sn = dlg.get("scene_number")
            if sn is not None:
                dialogue_by_scene.setdefault(sn, []).append(dlg)

        # Process each JSON scene
        for json_scene in json_scenes:
            scene_num = json_scene.get("scene_number")
            if scene_num is None:
                result.warnings.append("Scene without scene_number skipped")
                continue

            existing = scene_map.get(scene_num)

            if existing and update_existing:
                self._update_scene_from_json(existing, json_scene)
                result.scenes_updated += 1
            elif not existing and create_missing:
                new_scene = self._create_scene_from_json(script, json_scene)
                self.db.add(new_scene)
                self.db.flush()
                scene_map[scene_num] = new_scene
                result.scenes_created += 1

            # Create beats from dialogues
            if create_missing:
                scene = scene_map.get(scene_num)
                if scene:
                    dialogues = dialogue_by_scene.get(scene_num, [])
                    for i, dlg in enumerate(dialogues):
                        beat = self._create_beat_from_dialogue(scene, dlg, i)
                        self.db.add(beat)
                        result.beats_created += 1

        self.db.commit()
        result.message = (
            f"Synced JSON to structure: {result.scenes_created} scenes created, "
            f"{result.scenes_updated} updated, {result.beats_created} beats created"
        )
        return result

    def structure_to_json(
        self,
        script: "Script",
        scenes: Sequence["Scene"] | None = None,
    ) -> SyncResult:
        """
        Sync from story_structure tables to Script JSON.

        Args:
            script: Script model instance
            scenes: Optional list of Scene models (loaded if not provided)
        """
        from app.models.story_structure import Scene as SceneModel
        from app.models.story_structure import SceneBeat as SceneBeatModel

        result = SyncResult(success=True, message="")

        # Load scenes if not provided
        if scenes is None:
            scenes = (
                self.db.query(SceneModel)
                .filter(
                    SceneModel.script_id == script.id,
                    SceneModel.is_deleted.is_(False),
                )
                .order_by(SceneModel.scene_number)
                .all()
            )

        if not scenes:
            result.message = "No scenes in story_structure"
            return result

        # Build new JSON scenes
        new_scenes: list[dict[str, Any]] = []
        new_dialogues: list[dict[str, Any]] = []

        for scene in scenes:
            scene_dict = self._scene_to_json(scene)
            new_scenes.append(scene_dict)

            # Load beats
            beats = (
                self.db.query(SceneBeatModel)
                .filter(SceneBeatModel.scene_id == scene.id)
                .order_by(SceneBeatModel.order_index)
                .all()
            )

            for beat in beats:
                if beat.beat_type == "dialogue":
                    dlg_dict = self._beat_to_dialogue_json(scene, beat)
                    new_dialogues.append(dlg_dict)

        # Update Script JSON
        script.scenes = new_scenes
        script.dialogues = new_dialogues
        self.db.add(script)
        self.db.commit()

        result.json_updated = True
        result.message = (
            f"Synced structure to JSON: {len(new_scenes)} scenes, "
            f"{len(new_dialogues)} dialogues"
        )
        return result

    def reconcile(
        self,
        script: "Script",
        *,
        prefer_source: str = "structure",
    ) -> SyncResult:
        """
        Bidirectional reconciliation preferring specified source.

        Args:
            script: Script model instance
            prefer_source: Which source to prefer ('json' or 'structure')
        """
        from app.models.story_structure import Scene as SceneModel

        result = SyncResult(success=True, message="")

        # Load current state
        json_scenes = script.scenes if isinstance(script.scenes, list) else []
        structure_scenes = (
            self.db.query(SceneModel)
            .filter(
                SceneModel.script_id == script.id,
                SceneModel.is_deleted.is_(False),
            )
            .order_by(SceneModel.scene_number)
            .all()
        )

        json_count = len(json_scenes)
        struct_count = len(structure_scenes)

        # Determine sync direction
        if json_count == 0 and struct_count > 0:
            return self.structure_to_json(script, structure_scenes)
        elif struct_count == 0 and json_count > 0:
            return self.json_to_structure(script, create_missing=True)
        elif json_count == 0 and struct_count == 0:
            result.message = "No data in either source"
            return result

        # Both have data - reconcile based on preference
        if prefer_source == "structure":
            result = self.structure_to_json(script, structure_scenes)
        else:
            result = self.json_to_structure(
                script, create_missing=True, update_existing=True
            )

        result.message = f"Reconciled using {prefer_source} as primary source"
        return result

    def _create_scene_from_json(
        self,
        script: "Script",
        json_scene: dict[str, Any],
    ) -> "Scene":
        """Create Scene model from JSON dict."""
        from app.models.story_structure import Scene as SceneModel

        scene_num = json_scene.get("scene_number", 1)
        location = json_scene.get("location") or ""
        time = json_scene.get("time") or ""

        slug_line = f"INT. {location} - {time}".strip(" -")
        if not slug_line or slug_line == "INT.":
            slug_line = f"SCENE {scene_num}"

        return SceneModel(
            script_id=script.id,
            scene_number=str(scene_num),
            slug_line=slug_line,
            location=location,
            time_of_day=time,
            summary=json_scene.get("description"),
            primary_characters=json_scene.get("characters"),
            status="draft",
        )

    def _update_scene_from_json(
        self,
        scene: "Scene",
        json_scene: dict[str, Any],
    ) -> None:
        """Update existing Scene from JSON."""
        if json_scene.get("location"):
            scene.location = json_scene["location"]
        if json_scene.get("time"):
            scene.time_of_day = json_scene["time"]
        if json_scene.get("description"):
            scene.summary = json_scene["description"]
        if json_scene.get("characters"):
            scene.primary_characters = json_scene["characters"]
        scene.updated_at = datetime.now(timezone.utc)

    def _create_beat_from_dialogue(
        self,
        scene: "Scene",
        dialogue: dict[str, Any],
        order_index: int,
    ) -> "SceneBeat":
        """Create SceneBeat from dialogue dict."""
        from app.models.story_structure import SceneBeat as SceneBeatModel

        character = dialogue.get("character") or "旁白"
        content = dialogue.get("content") or ""

        return SceneBeatModel(
            scene_id=scene.id,
            order_index=order_index,
            beat_type="dialogue",
            dialogue_excerpt=content,
            characters_involved=[character],
            beat_summary=f"{character}: {content[:50]}..." if len(content) > 50 else f"{character}: {content}",
        )

    def _scene_to_json(self, scene: "Scene") -> dict[str, Any]:
        """Convert Scene model to JSON dict."""
        try:
            scene_num = int(str(scene.scene_number).strip())
        except (ValueError, TypeError):
            scene_num = None

        return {
            "scene_number": scene_num,
            "location": scene.location,
            "time": scene.time_of_day,
            "description": scene.summary,
            "characters": scene.primary_characters,
        }

    def _beat_to_dialogue_json(
        self,
        scene: "Scene",
        beat: "SceneBeat",
    ) -> dict[str, Any]:
        """Convert dialogue beat to JSON dict."""
        try:
            scene_num = int(str(scene.scene_number).strip())
        except (ValueError, TypeError):
            scene_num = None

        chars = beat.characters_involved or []
        character = chars[0] if chars else "旁白"

        return {
            "scene_number": scene_num,
            "character": character,
            "content": beat.dialogue_excerpt or "",
            "emotion": None,
            "action": None,
        }
