"""LLM invocation for batched dynamic storyboard prompt generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.storyboard_dynamic_prompt import DynamicPromptBatch
from app.utils.json_utils import extract_json_block

logger = get_logger("storyboard_dynamic_prompt")


async def generate_prompts_for_scene(
    scene_context: Dict[str, Any],
    frame_inputs: List[Dict[str, Any]],
    *,
    ai_manager: Any,
    model: Optional[str] = None,
) -> Dict[int, Dict[str, str]]:
    """Call the LLM once for a chunk of frames; return frame_index -> prompts.

    Returns an empty dict when generation or parsing fails (after one retry);
    callers fall back to the compiler output per missing frame.
    """
    if not frame_inputs:
        return {}
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_DYNAMIC_IMAGE_PROMPT.value,
        {**scene_context, "frames": frame_inputs},
    )
    schema = DynamicPromptBatch.model_json_schema()
    system_prompt = prompt_manager.render_prompt(
        PromptTemplate.SYSTEM_PROMPT_JSON_STRICT.value, {}
    )
    expected = {int(item["frame_index"]) for item in frame_inputs}

    for attempt in range(2):
        try:
            response = await ai_manager.generate_text(
                prompt=prompt,
                temperature=0.5,
                model=model,
                json_schema={"name": "storyboard_frame_prompts", "schema": schema},
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.warning(
                "dynamic prompt LLM call failed (attempt %s): %s", attempt + 1, exc
            )
            continue
        if not getattr(response, "success", False):
            logger.warning(
                "dynamic prompt LLM unsuccessful (attempt %s): %s",
                attempt + 1,
                getattr(response, "error", None),
            )
            continue
        parsed = _parse_batch(response.data, expected)
        if parsed:
            for bundle in parsed.values():
                bundle["provider_used"] = getattr(response, "provider", None)
                bundle["model_used"] = getattr(response, "model", None)
            return parsed
        logger.warning("dynamic prompt JSON invalid (attempt %s)", attempt + 1)
    return {}


def _parse_batch(
    data: Any, expected_indexes: set
) -> Dict[int, Dict[str, str]]:
    content = data if isinstance(data, str) else str(data)
    normalized = extract_json_block(content)
    if not normalized:
        return {}
    try:
        batch = DynamicPromptBatch.model_validate(normalized)
    except Exception:
        return {}
    results: Dict[int, Dict[str, str]] = {}
    for item in batch.frames:
        if item.frame_index not in expected_indexes:
            continue
        if not (
            item.image_prompt.strip()
            and item.start_keyframe_prompt.strip()
            and item.end_keyframe_prompt.strip()
        ):
            continue
        results[item.frame_index] = {
            "image_prompt": item.image_prompt.strip(),
            "start_keyframe_prompt": item.start_keyframe_prompt.strip(),
            "end_keyframe_prompt": item.end_keyframe_prompt.strip(),
        }
    return results
