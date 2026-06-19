from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List


def log_beat_contract_generation_error(owner: Any, exc: Exception) -> None:
    logger = getattr(owner, "logger", None)
    if logger:
        logger.warning(
            "AI manager beat contract generation failed: %s",
            exc,
            exc_info=True,
        )
        return
    logging.getLogger(__name__).warning(
        "AI manager beat contract generation failed: %s",
        exc,
        exc_info=True,
    )


def build_ai_manager_script_result(
    *,
    beat_result: Dict[str, Any],
    story: Dict[str, Any],
    episode: Dict[str, Any],
    language: str,
    format_type: str,
    scene_detail_level: str,
    style_preferences: List[str],
    template_style: str,
    target_chars_per_episode: int,
    quality_threshold: float,
    generation_mode: str,
    build_script_text: Callable[..., str],
) -> Dict[str, Any]:
    flattened = beat_result["payload"]
    response = beat_result["response"]
    payload = _script_payload(
        flattened=flattened,
        story=story,
        episode=episode,
        language=language,
        format_type=format_type,
        scene_detail_level=scene_detail_level,
        style_preferences=style_preferences,
        template_style=template_style,
        target_chars_per_episode=target_chars_per_episode,
        quality_threshold=quality_threshold,
        generation_mode=generation_mode,
        response=response,
    )
    payload["content"] = build_script_text(
        payload.get("scenes") or [],
        payload.get("dialogues") or [],
        payload.get("stage_directions") or [],
        format_type=format_type,
        language=language,
        episode_number=episode.get("episode_number"),
        template_style=template_style,
        target_chars_per_episode=target_chars_per_episode,
        title=episode.get("title"),
    )
    payload["metadata"]["structured_script_contract"] = payload[
        "structured_script_contract"
    ]

    return {
        "content": payload,
        "normalized": payload,
        "prompt": beat_result["prompt"],
        "generation_method": f"ai_manager_{response.provider}",
        "template_used": "script_beats",
        "provider_used": response.provider,
        "model_used": response.model,
        "usage": response.usage,
    }


def _script_payload(
    *,
    flattened: Dict[str, Any],
    story: Dict[str, Any],
    episode: Dict[str, Any],
    language: str,
    format_type: str,
    scene_detail_level: str,
    style_preferences: List[str],
    template_style: str,
    target_chars_per_episode: int,
    quality_threshold: float,
    generation_mode: str,
    response: Any,
) -> Dict[str, Any]:
    return {
        "content": flattened["content"],
        "scenes": flattened["scenes"],
        "dialogues": flattened["dialogues"],
        "stage_directions": flattened["stage_directions"],
        "metadata": {
            **_base_metadata(
                story=story,
                episode=episode,
                response=response,
                language=language,
                format_type=format_type,
                scene_detail_level=scene_detail_level,
                style_preferences=style_preferences,
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                quality_threshold=quality_threshold,
                generation_mode=generation_mode,
            ),
            **flattened.get("metadata", {}),
        },
        "structured_script_contract": flattened["structured_script_contract"],
    }


def _base_metadata(
    *,
    story: Dict[str, Any],
    episode: Dict[str, Any],
    response: Any,
    language: str,
    format_type: str,
    scene_detail_level: str,
    style_preferences: List[str],
    template_style: str,
    target_chars_per_episode: int,
    quality_threshold: float,
    generation_mode: str,
) -> Dict[str, Any]:
    return {
        "story_title": story.get("title"),
        "episode_title": episode.get("title"),
        "generator": f"ai_manager:{response.provider}",
        "language": language,
        "format_type": format_type,
        "scene_detail_level": scene_detail_level,
        "style_preferences": style_preferences,
        "template_style": template_style,
        "target_chars_per_episode": target_chars_per_episode,
        "quality_threshold": quality_threshold,
        "generation_mode": generation_mode,
        "market_region": story.get("market_region") or episode.get("market_region"),
        "micro_genre": story.get("micro_genre") or episode.get("micro_genre"),
        "hook_plan": story.get("hook_plan") or episode.get("hook_plan"),
        "twist_density": story.get("twist_density") or episode.get("twist_density"),
        "cliffhanger_plan": story.get("cliffhanger_plan")
        or episode.get("cliffhanger_plan"),
        "ad_snippets": story.get("ad_snippets") or episode.get("ad_snippets"),
    }
