"""Audio timeline -> storyboard context enrichment.

Inject:
- Story character card briefs (appearance/clothing anchors) into `prompt_description`
- Auto-selected `reference_images` (<=3: character anchors + environment)

So video generation (e.g. Veo) can keep identity stable without first generating
storyboard images.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from app.core.validators.character_registry import (
    GENERIC_ROLE_BASES,
    normalize_character_name_token,
    normalize_to_registered_or_generic,
)
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from sqlalchemy.orm import Session

from .storyboard_audio_character_visuals import load_story_character_visuals
from .storyboard_audio_context_utils import compact, dedupe_strs, truncate
from .storyboard_audio_scene_env_hints import load_scene_environment_hints


def enrich_storyboard_frames_with_story_context(
    db: Session,
    *,
    story_id: int,
    script_id: int,
    frames: Sequence[Dict[str, Any]],
    max_reference_images: int = 3,
    max_character_cards: int = 3,
    update_prompt_context: bool = True,
) -> None:
    """Mutate storyboard frames in-place with story character cards + reference images."""
    max_reference_images = max(0, min(int(max_reference_images), 3))
    max_character_cards = max(0, int(max_character_cards))

    visuals, alias_to_canonical = load_story_character_visuals(db, story_id=story_id)

    scene_ids: list[int] = []
    scene_numbers: list[int] = []
    for frame in frames or []:
        if not isinstance(frame, dict):
            continue
        sid = frame.get("scene_id")
        if isinstance(sid, int):
            scene_ids.append(sid)
        sn = frame.get("scene_number")
        if isinstance(sn, int):
            scene_numbers.append(sn)

    env_by_id, env_by_number = load_scene_environment_hints(
        db,
        script_id=script_id,
        scene_ids=scene_ids,
        scene_numbers=scene_numbers,
    )

    for frame in frames or []:
        if not isinstance(frame, dict):
            continue

        raw_chars = frame.get("characters")
        normalized: list[str] = []
        if isinstance(raw_chars, list):
            for item in raw_chars:
                token = normalize_character_name_token(
                    str(item) if item is not None else ""
                )
                if not token:
                    continue
                canonical = normalize_to_registered_or_generic(
                    token, alias_to_canonical=alias_to_canonical
                )
                if not canonical or canonical in normalized:
                    continue
                normalized.append(canonical)

        context_text = _frame_character_context(frame).casefold()
        if context_text:
            for alias, canonical in alias_to_canonical.items():
                if (
                    len(alias.strip()) >= 2
                    and alias.casefold() in context_text
                    and canonical in visuals
                    and canonical not in normalized
                ):
                    normalized.append(canonical)

        prompt_chars = [c for c in normalized if c not in GENERIC_ROLE_BASES]
        frame["characters"] = prompt_chars

        idx_by_name = {name: idx for idx, name in enumerate(prompt_chars)}

        def _importance(name: str) -> int:
            visual = visuals.get(name)
            return int(getattr(visual, "importance", 0) or 0) if visual else 0

        ordered_chars = sorted(
            prompt_chars,
            key=lambda name: (_importance(name), -idx_by_name.get(name, 0)),
            reverse=True,
        )

        # Character cards (cap) for this frame.
        card_lines: list[str] = []
        if max_character_cards > 0:
            for name in ordered_chars:
                visual = visuals.get(name)
                if visual and visual.card_brief:
                    card_lines.append(visual.card_brief)
                if len(card_lines) >= max_character_cards:
                    break

        scene_id = frame.get("scene_id")
        scene_number = frame.get("scene_number")
        env_url: Optional[str] = None
        env_hint: Optional[str] = None
        if isinstance(scene_id, int) and scene_id in env_by_id:
            env_url, env_hint = env_by_id.get(scene_id) or (None, None)
        elif isinstance(scene_number, int) and scene_number in env_by_number:
            env_url, env_hint = env_by_number.get(scene_number) or (None, None)

        # Auto-select reference_images unless caller already provided them.
        existing_refs = frame.get("reference_images")
        has_existing = isinstance(existing_refs, list) and any(
            isinstance(x, str) and x.strip() for x in existing_refs
        )
        if not has_existing and max_reference_images > 0:
            char_refs: list[str] = []
            for name in ordered_chars:
                visual = visuals.get(name)
                if (
                    visual
                    and isinstance(visual.anchor_url, str)
                    and visual.anchor_url.strip()
                ):
                    char_refs.append(visual.anchor_url.strip())
            char_refs = dedupe_strs(char_refs)

            selected: list[str] = []
            if env_url and isinstance(env_url, str) and env_url.strip():
                max_char = max(0, max_reference_images - 1)
                selected = char_refs[:max_char] + [env_url.strip()]
            else:
                selected = char_refs[:max_reference_images]

            frame["reference_images"] = (
                dedupe_strs(selected)[:max_reference_images] or None
            )

        # Merge context into visual-only prompt_description via template.
        base = str(
            frame.get("prompt_description") or frame.get("description") or ""
        ).strip()
        env_text = truncate(env_hint or "", 160) if env_hint else None
        if update_prompt_context and base and (card_lines or env_text):
            rendered = prompt_manager.render_prompt(
                PromptTemplate.STORYBOARD_AUDIO_VISUAL_CONTEXT.value,
                {
                    "base": base,
                    "character_cards": card_lines,
                    "environment": env_text,
                },
            )
            frame["prompt_description"] = compact(rendered)


def _frame_character_context(frame: Dict[str, Any]) -> str:
    values = [
        frame.get(key)
        for key in (
            "description",
            "beat_text",
            "speaker_name",
        )
    ]
    shot_plan = frame.get("timeline_shot_plan")
    if isinstance(shot_plan, dict):
        values.extend(value for value in shot_plan.values() if isinstance(value, str))
    return "\n".join(value for value in values if isinstance(value, str))
