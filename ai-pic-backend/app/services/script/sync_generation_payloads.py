"""Payload helpers for synchronous script generation."""

from __future__ import annotations

from typing import Any, Dict

from app.schemas.generation_requests import ScriptGenerationRequest
from app.utils.json_utils import extract_json_block
from app.utils.script_parser import extract_script_structure


def parse_ai_content(result: Dict[str, Any]) -> Dict[str, Any]:
    raw_content = result.get("content")
    if isinstance(raw_content, dict):
        return raw_content
    parsed = extract_json_block(raw_content)
    if parsed:
        return parsed
    source_text = raw_content or ""
    extracted = extract_script_structure(source_text)
    return {
        "content": extracted.get("content", source_text),
        "scenes": extracted.get("scenes", []),
        "dialogues": extracted.get("dialogues", []),
        "stage_directions": extracted.get("stage_directions", []),
        "metadata": extracted.get("metadata", {}),
    }


def build_agent_run(result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    return {
        "generation_method": result.get("generation_method"),
        "template_used": result.get("template_used"),
        "provider_used": result.get("provider_used"),
        "model_used": result.get("model_used"),
        "usage": result.get("usage"),
        "reasoning": result.get("reasoning"),
    }


def split_model_provider(model: str | None) -> tuple[str | None, str | None]:
    if model and ":" in model:
        provider, model_id = model.split(":", 1)
        return provider, model_id
    return None, model


def build_marketing_overrides(request: ScriptGenerationRequest) -> Dict[str, Any]:
    return {
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "hook_plan": request.hook_plan.model_dump() if request.hook_plan else None,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan,
        "ad_snippets": (
            [snippet.model_dump() for snippet in request.ad_snippets]
            if request.ad_snippets
            else None
        ),
    }


def build_generation_params(request: ScriptGenerationRequest) -> Dict[str, Any]:
    return {
        "generation_mode": request.generation_mode,
        "auto_timeline_pipeline": request.auto_timeline_pipeline,
        "dialogue_style": request.dialogue_style,
        "scene_detail_level": request.scene_detail_level,
        "template_style": request.template_style,
        "target_chars_per_episode": request.target_chars_per_episode,
        "quality_threshold": request.quality_threshold,
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "hook_plan": request.hook_plan.model_dump() if request.hook_plan else None,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan,
        "ad_snippets": (
            [snippet.model_dump() for snippet in request.ad_snippets]
            if request.ad_snippets
            else None
        ),
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences,
        "model": request.model,
        "temperature": request.temperature or 0.7,
    }
