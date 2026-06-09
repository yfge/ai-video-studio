"""Context-aware prompt helpers for clip storyboard sheets and panels."""

from __future__ import annotations

from typing import Any, Mapping

from app.services.storyboard.storyboard_prompt_compiler import StoryboardPromptCompiler


def panel_motion_prompt(panel: Mapping[str, Any]) -> str:
    frame = {
        "timeline_clip_id": panel.get("clip_id"),
        "description": panel.get("visual_prompt") or panel.get("video_prompt") or "",
        "camera_movement": panel.get("camera_movement"),
        "beat_text": panel.get("video_prompt") or panel.get("visual_prompt") or "",
        "shot_plan_prompt_layers": {
            "camera_movement": panel.get("camera_movement"),
            "motion_timeline": panel.get("motion_timeline"),
            "emotional_landing": panel.get("emotional_landing"),
        },
    }
    return StoryboardPromptCompiler().compile_frame(frame)["i2v_motion_prompt"]


def bound_context_lines(panel: Mapping[str, Any]) -> list[str]:
    context = panel.get("bound_context")
    if not isinstance(context, Mapping):
        return []
    lines: list[str] = []
    lines.extend(_character_lines(context))
    environment = context.get("environment")
    if isinstance(environment, Mapping):
        hint = environment.get("hint")
        if isinstance(hint, str) and hint.strip():
            lines.append(f"Environment anchor: {hint.strip()}.")
    roles = reference_roles(context)
    if roles:
        lines.append(f"Reference image roles: {roles}.")
    warnings = context.get("warnings")
    if isinstance(warnings, list) and warnings:
        cleaned = [str(w).strip() for w in warnings if str(w).strip()]
        if cleaned:
            lines.append(f"Context warnings: {', '.join(cleaned)}.")
    return lines


def panel_context_text(panel: Mapping[str, Any]) -> str:
    return " ".join(bound_context_lines(panel))


def reference_roles(context: Mapping[str, Any]) -> str:
    roles: list[str] = []
    characters = context.get("characters")
    if isinstance(characters, list):
        for character in characters:
            if isinstance(character, Mapping) and character.get("anchor_url"):
                name = str(character.get("name") or "character").strip()
                roles.append(f"{name} character anchor")
    environment = context.get("environment")
    if isinstance(environment, Mapping) and environment.get("reference_url"):
        roles.append("environment anchor")
    return " | ".join(roles)


def _character_lines(context: Mapping[str, Any]) -> list[str]:
    characters = context.get("characters")
    if not isinstance(characters, list) or not characters:
        return []
    names = [
        str(character.get("name")).strip()
        for character in characters
        if isinstance(character, Mapping) and character.get("name")
    ]
    return [f"Character anchors: {', '.join(names)}."] if names else []
