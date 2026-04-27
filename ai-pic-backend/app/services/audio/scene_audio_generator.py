"""Scene dialogue audio generator.

Generates TTS audio tracks for individual scenes, computing
context-aware pause durations between dialogue segments.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.ai_service import ai_service
from app.services.audio.audio_generator import ensure_oss_configured
from app.services.audio.dialogue_processing.prose_dialogue_splitter import (
    repair_scene_dialogues_for_audio,
    sanitize_stage_directions_for_audio,
)
from app.services.audio.dialogue_processing.scene_extractors import (
    extract_dialogues_for_scene,
    extract_scene_number,
    extract_stage_for_scene,
)
from app.services.audio.dialogue_processor import plan_scene_segments_intelligent
from app.services.audio.scene_audio_assembler import assemble_scene_audio
from app.services.audio.scene_tts_phase import (
    compress_dialogue_tts_to_target,
    generate_dialogue_tts_phase,
)
from app.services.script.script_character_policy import build_story_alias_map
from app.services.voice_binding_service import get_story_character_map
from sqlalchemy.orm import Session

logger = get_logger(__name__)


async def generate_scene_dialogue_audio(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scene: Scene,
    tts_model: str = "speech-2.6-hd",
    overwrite_beats: bool = True,
    use_intelligent_timing: bool = True,
    timing_model: str | None = None,
    target_duration_seconds: int | None = None,
) -> dict[str, Any]:
    """Generate 1 dialogue audio track per scene and persist beats.

    Two-phase flow for accurate duration control:
    1. Generate TTS for all dialogues first -> get actual durations
    2. Call Timeline Agent with actual durations -> compute GAPs dynamically
    3. Assemble audio with computed GAPs
    """
    ensure_oss_configured()

    scene_number = extract_scene_number(scene)
    dialogues = extract_dialogues_for_scene(script, scene_number)
    stage = extract_stage_for_scene(script, scene_number)
    scene_context = _build_scene_context(scene, scene_number)

    story_char_map = get_story_character_map(db, story.id)
    alias_to_canonical = build_story_alias_map(story)
    dialogues = repair_scene_dialogues_for_audio(
        dialogues, alias_to_canonical=alias_to_canonical
    )
    stage = sanitize_stage_directions_for_audio(
        stage, alias_to_canonical=alias_to_canonical
    )
    scene_character_names = _collect_character_names(dialogues)

    with tempfile.TemporaryDirectory(prefix="scene-audio-") as tmp_root:
        tmp_root_path = Path(tmp_root)

        tts_results, total_ms = await generate_dialogue_tts_phase(
            db,
            dialogues,
            story_char_map,
            story,
            episode,
            scene,
            script,
            tts_model,
            tmp_root_path,
        )
        if target_duration_seconds and tts_results:
            total_ms = compress_dialogue_tts_to_target(
                tts_results,
                total_ms,
                target_duration_seconds,
                scene,
                scene_number,
                tmp_root_path,
            )
        segments = await _phase2_gaps(
            dialogues,
            tts_results,
            stage,
            scene_context,
            use_intelligent_timing,
            total_ms,
            target_duration_seconds,
            timing_model,
            scene,
        )
        return await assemble_scene_audio(
            db,
            segments=segments,
            dialogue_tts_results=tts_results,
            tmp_root_path=tmp_root_path,
            scene=scene,
            episode=episode,
            script=script,
            story=story,
            story_char_map=story_char_map,
            scene_number=scene_number,
            scene_character_names=scene_character_names,
            tts_model=tts_model,
            overwrite_beats=overwrite_beats,
            target_duration_seconds=target_duration_seconds,
        )


def _build_scene_context(scene: Scene, scene_number: int) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "scene_id": scene.id,
        "scene_number": scene_number,
        "slug_line": getattr(scene, "slug_line", None),
        "location": getattr(scene, "location", None),
        "time_of_day": getattr(scene, "time_of_day", None),
        "summary": getattr(scene, "summary", None),
        "primary_characters": getattr(scene, "primary_characters", None),
        "conflict_notes": getattr(scene, "conflict_notes", None),
        "dramatic_question": None,
    }
    if hasattr(scene, "step_outline") and scene.step_outline:
        ctx["dramatic_question"] = getattr(
            scene.step_outline, "dramatic_question", None
        )
    return ctx


def _collect_character_names(dialogues: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for dlg in dialogues or []:
        if not isinstance(dlg, dict):
            continue
        name = (dlg.get("character") or "").strip()
        if not name or name == "旁白" or name in names:
            continue
        names.append(name)
    return names


async def _phase2_gaps(
    dialogues: list[dict[str, Any]],
    tts_results: list[dict[str, Any]],
    stage: list[dict[str, Any]],
    scene_context: dict[str, Any],
    use_intelligent_timing: bool,
    total_dialogue_ms: int,
    target_duration_seconds: int | None,
    timing_model: str | None,
    scene: Scene,
) -> list:
    """Phase 2: Compute GAPs with actual durations via Timeline Agent."""
    dialogues_with_duration = []
    for dlg in dialogues:
        dlg_copy = dict(dlg)
        for tts_res in tts_results:
            if tts_res["content"] == dlg.get("content"):
                dlg_copy["actual_duration_ms"] = tts_res["actual_duration_ms"]
                break
        dialogues_with_duration.append(dlg_copy)

    if target_duration_seconds:
        target_ms = target_duration_seconds * 1000
        logger.info(
            "Phase 2: Computing GAPs with actual dialogue durations",
            extra={
                "scene_id": scene.id,
                "total_dialogue_duration_ms": total_dialogue_ms,
                "available_gap_ms": target_ms - total_dialogue_ms,
                "dialogue_count": len(tts_results),
            },
        )

    action_base_ms, action_per_char_ms = 800, 20
    action_max_ms, pause_after_ms = 3000, 300
    effective_stage = stage
    effective_timing = use_intelligent_timing

    if target_duration_seconds:
        target_ms = int(target_duration_seconds * 1000)
        if total_dialogue_ms >= target_ms:
            pause_after_ms = 0
            effective_timing = False
            if stage:
                combined = "；".join(
                    str(s.get("content") or "").strip()
                    for s in stage
                    if isinstance(s, dict) and str(s.get("content") or "").strip()
                ).strip()
                if combined:
                    effective_stage = [{"content": combined[:300], "timing": "mid"}]
                    action_base_ms, action_per_char_ms, action_max_ms = 1000, 0, 1000
                else:
                    effective_stage = []
                    action_base_ms = action_per_char_ms = action_max_ms = 0
            else:
                effective_stage = []
                action_base_ms = action_per_char_ms = action_max_ms = 0

    return await plan_scene_segments_intelligent(
        dialogues=dialogues_with_duration,
        stage_directions=effective_stage,
        scene_context=scene_context,
        ai_service=ai_service,
        use_intelligent_timing=effective_timing,
        pause_after_dialogue_ms=pause_after_ms,
        action_base_ms=action_base_ms,
        action_per_char_ms=action_per_char_ms,
        action_max_ms=action_max_ms,
        timing_model=timing_model,
        target_duration_seconds=target_duration_seconds,
    )
