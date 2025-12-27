from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from app.models.story import Story


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def populate_dialogues_and_stage_if_missing(
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    *,
    story: "Story | None" = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Populate missing dialogues/stage_directions in a non-misleading way.

    Rationale:
    - Some LLM runs may return incomplete dialogues (e.g., missing early scenes).
    - Downstream pipelines (audio/timeline/storyboard) should not be blocked by
      empty lists, but we must avoid inserting generic "fake" dialogues that
      look valid yet are obviously wrong to users.

    Policy:
    - If a scene has no dialogue lines, add a single narration line derived from
      the scene summary/description (character="旁白"). This is at least
      story-consistent and clearly a narration fallback.
    - If a scene has no stage direction, add an action stage direction using
      the same summary/description.
    """
    scene_numbers_with_dialogues: set[int] = set()
    for dlg in dialogues or []:
        if not isinstance(dlg, dict):
            continue
        scene_no = _to_int(dlg.get("scene_number"))
        if scene_no:
            scene_numbers_with_dialogues.add(scene_no)

    scene_numbers_with_stage: set[int] = set()
    for sd in stage_directions or []:
        if not isinstance(sd, dict):
            continue
        scene_no = _to_int(sd.get("scene_number"))
        if scene_no:
            scene_numbers_with_stage.add(scene_no)

    missing_dialogue_scenes: List[tuple[int, Dict[str, Any]]] = []
    missing_stage_scenes: List[tuple[int, Dict[str, Any]]] = []
    for idx, sc in enumerate(scenes, start=1):
        if not isinstance(sc, dict):
            continue
        scene_no = _to_int(sc.get("scene_number")) or idx
        if scene_no not in scene_numbers_with_dialogues:
            missing_dialogue_scenes.append((scene_no, sc))
        if scene_no not in scene_numbers_with_stage:
            missing_stage_scenes.append((scene_no, sc))

    if (
        dialogues
        and stage_directions
        and not missing_dialogue_scenes
        and not missing_stage_scenes
    ):
        return dialogues, stage_directions

    generated_dialogues: List[Dict[str, Any]] = list(dialogues) if dialogues else []
    generated_stage: List[Dict[str, Any]] = (
        list(stage_directions) if stage_directions else []
    )

    for scene_no, sc in missing_dialogue_scenes:
        summary = (
            sc.get("summary")
            or sc.get("description")
            or sc.get("slug_line")
            or f"场景 {scene_no}"
        )
        generated_dialogues.append(
            {
                "scene_number": scene_no,
                "character": "旁白",
                "content": str(summary),
                "fallback": True,
                "fallback_reason": "missing_dialogues",
            }
        )

    for scene_no, sc in missing_stage_scenes:
        summary = (
            sc.get("summary")
            or sc.get("description")
            or sc.get("slug_line")
            or f"场景 {scene_no}"
        )
        generated_stage.append(
            {
                "scene_number": scene_no,
                "timing": "mid",
                "content": str(summary),
                "type": "action",
                "fallback": True,
                "fallback_reason": "missing_stage_directions",
            }
        )

    return generated_dialogues, generated_stage
