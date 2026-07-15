"""Fingerprint-based caching of dynamic prompt bundles on storyboard frames."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

# Bump when the LLM template or context shape changes to invalidate all caches.
TEMPLATE_VERSION = "storyboard_dynamic_image_prompt:v3"

BUNDLE_KEY = "llm_prompt_bundle"
REQUIRED_PROMPT_FIELDS = (
    "image_prompt",
    "start_keyframe_prompt",
    "end_keyframe_prompt",
)


def compute_input_fingerprint(
    scene_context: Dict[str, Any], frame_input: Dict[str, Any]
) -> str:
    payload = {
        "template_version": TEMPLATE_VERSION,
        "scene_context": scene_context,
        "frame_input": frame_input,
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_cached_bundle(frame: dict, fingerprint: str) -> Optional[Dict[str, Any]]:
    """Return the cached bundle when its fingerprint matches and prompts exist."""
    bundle = frame.get(BUNDLE_KEY)
    if not isinstance(bundle, dict):
        return None
    if bundle.get("input_sha") != fingerprint:
        return None
    for field in REQUIRED_PROMPT_FIELDS:
        value = bundle.get(field)
        if not isinstance(value, str) or not value.strip():
            return None
    return bundle


def write_bundle(frame: dict, bundle: Dict[str, Any]) -> None:
    frame[BUNDLE_KEY] = bundle
