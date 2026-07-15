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
        lines.extend(roles)
    return lines


def panel_context_text(panel: Mapping[str, Any]) -> str:
    return " ".join(bound_context_lines(panel))


def reference_roles(context: Mapping[str, Any]) -> list[str]:
    bindings = context.get("reference_bindings")
    if isinstance(bindings, list) and bindings:
        lines = [_reference_binding_line(binding) for binding in bindings]
        return [line for line in lines if line]

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
    return [f"Reference image roles: {' | '.join(roles)}."] if roles else []


def _character_lines(context: Mapping[str, Any]) -> list[str]:
    characters = context.get("characters")
    if not isinstance(characters, list) or not characters:
        return []
    valid_characters = [
        character
        for character in characters
        if isinstance(character, Mapping) and character.get("name")
    ]
    names = [str(character.get("name")).strip() for character in valid_characters]
    if not names:
        return []
    lines = [
        f"Authoritative cast contract: show only these bound characters: {', '.join(names)}.",
        (
            "The bound cast contract overrides any inherited panel wording about "
            "person count, gender, age, face, hair, wardrobe, or identity."
        ),
        (
            "Do not add, remove, swap, duplicate, merge, gender-swap, or age-shift "
            "the bound characters between panels."
        ),
    ]
    for character in valid_characters:
        brief = str(
            character.get("appearance_brief") or character.get("card_brief") or ""
        ).strip()
        if brief:
            lines.append(f"Character appearance contract: {brief}.")
    return lines


def _reference_binding_line(binding: Any) -> str:
    if not isinstance(binding, Mapping):
        return ""
    index = binding.get("index")
    label = str(binding.get("label") or "reference").strip()
    role = str(binding.get("role") or "").strip()
    if not index:
        return ""
    if role == "character_identity":
        purpose = f"{label} identity anchor"
    elif role == "character_reference":
        purpose = f"{label} appearance reference"
    elif role == "environment":
        purpose = label
    else:
        purpose = label
    return f"Reference image {index} = {purpose}."
