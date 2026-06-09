"""Compile Timeline storyboard data into provider-ready prompt bundles."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.prompts.template_audit import sha256_text
from app.services.storyboard.storyboard_prompt_sections import (
    INLINE_CONSTRAINTS,
    build_clip_identity,
    build_i2v_motion_prompt,
    build_image_prompt,
    build_keyframe_prompt,
    first_text,
    prompt_layers,
    reference_note,
)

PROMPT_VERSION = "storyboard_prompt_v2"


class StoryboardPromptCompiler:
    """Build prompt variants without collapsing shot-plan structure."""

    def __init__(
        self,
        *,
        image_limit: int = 2200,
        keyframe_limit: int = 1800,
        motion_limit: int = 1400,
    ) -> None:
        self.image_limit = image_limit
        self.keyframe_limit = keyframe_limit
        self.motion_limit = motion_limit

    def compile_frame(
        self,
        frame: Mapping[str, Any],
        *,
        base_prompt: str | None = None,
        reference_notes: Sequence[Mapping[str, Any]] | None = None,
        provider: str | None = None,
        negative_prompt_supported: bool = True,
    ) -> dict[str, Any]:
        warnings: list[str] = []
        layers = prompt_layers(frame)
        subject = first_text(
            base_prompt,
            frame.get("prompt_description"),
            frame.get("ai_prompt"),
            frame.get("description"),
        )
        image_prompt = self._truncate(
            build_image_prompt(
                frame,
                layers,
                subject=subject,
                reference_notes=reference_notes or [],
            ),
            self.image_limit,
            "image_prompt_truncated",
            warnings,
        )
        start_prompt = self._truncate(
            build_keyframe_prompt(image_prompt, layers, role="start"),
            self.keyframe_limit,
            "start_keyframe_prompt_truncated",
            warnings,
        )
        end_prompt = self._truncate(
            build_keyframe_prompt(image_prompt, layers, role="end"),
            self.keyframe_limit,
            "end_keyframe_prompt_truncated",
            warnings,
        )
        motion_prompt = self._truncate(
            build_i2v_motion_prompt(frame, layers),
            self.motion_limit,
            "i2v_motion_prompt_truncated",
            warnings,
        )
        provider_constraints = {
            "provider": provider,
            "negative_prompt_supported": bool(negative_prompt_supported),
            "inline_constraints": INLINE_CONSTRAINTS,
        }
        if not negative_prompt_supported:
            warnings.append("negative_prompt not supported; constraints inlined")

        return {
            "version": PROMPT_VERSION,
            "clip_identity": build_clip_identity(frame),
            "image_prompt": image_prompt,
            "start_keyframe_prompt": start_prompt,
            "end_keyframe_prompt": end_prompt,
            "i2v_motion_prompt": motion_prompt,
            "reference_notes": [reference_note(note) for note in reference_notes or []],
            "provider_constraints": provider_constraints,
            "prompt_sha256": sha256_text(image_prompt),
            "warnings": warnings,
        }

    @staticmethod
    def _truncate(
        text: str,
        limit: int,
        warning: str,
        warnings: list[str],
    ) -> str:
        if len(text) <= limit:
            return text
        warnings.append(warning)
        return text[: limit - 3].rstrip() + "..."
