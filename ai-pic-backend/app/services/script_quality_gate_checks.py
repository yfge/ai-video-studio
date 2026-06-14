from __future__ import annotations

from typing import Any, Dict, Optional

from app.schemas.generation import ScriptModel
from app.schemas.script_quality import ScriptLintOptions
from app.services.narrative_context import extract_story_characters
from app.services.quality_gate_core import make_quality_check
from app.services.script_quality import lint_script_content_async
from app.services.validators.script_quality_validator import ScriptQualityValidator


def schema_check(content: Dict[str, Any]) -> Dict[str, Any]:
    try:
        ScriptModel.model_validate(content)
        return make_quality_check("script_schema", True, "script schema valid")
    except Exception as exc:
        return make_quality_check(
            "script_schema",
            False,
            "script schema invalid",
            details={"error": str(exc)},
        )


def story_model_character_check(
    story_model: Any,
    episode_id: Optional[int],
    db: Any,
    scenes: list[Dict[str, Any]],
    dialogues: list[Dict[str, Any]],
) -> Dict[str, Any]:
    from app.services.script.script_character_policy import (
        enforce_script_character_policy,
    )

    policy = enforce_script_character_policy(
        story=story_model,
        scenes=scenes,
        dialogues=dialogues,
        episode_id=episode_id,
        db=db,
    )
    return make_quality_check(
        "script_character_policy",
        not policy.unknown_names,
        "script speakers must be registered story or episode characters",
        details={
            "unknown_names": policy.unknown_names,
            "canonical_names": policy.canonical_names,
        },
    )


def fallback_dialogue_check(dialogues: list[Dict[str, Any]]) -> Dict[str, Any]:
    fallback_lines = [
        {
            "scene_number": item.get("scene_number"),
            "character": item.get("character"),
            "content": item.get("content"),
            "fallback_reason": item.get("fallback_reason"),
        }
        for item in dialogues
        if isinstance(item, dict) and item.get("fallback")
    ]
    return make_quality_check(
        "script_dialogue_fallback",
        not fallback_lines,
        "fallback narration cannot pass as dialogue",
        details={"fallback_lines": fallback_lines},
    )


def dict_character_check(
    story: Dict[str, Any], dialogues: list[Dict[str, Any]]
) -> Dict[str, Any]:
    characters = extract_story_characters(story)
    known = {str(c.get("name")).strip() for c in characters if c.get("name")}
    generic = {"旁白", "路人", "店员", "服务员", "医生", "护士", "警察"}
    unknown: set[str] = set()
    if known:
        for dialogue in dialogues:
            speaker = str(dialogue.get("character") or "旁白").strip()
            if speaker and speaker not in known and not _is_generic(speaker, generic):
                unknown.add(speaker)
    return make_quality_check(
        "script_characters",
        not unknown,
        "script speakers must match story characters",
        details={"unknown_names": sorted(unknown), "known_names": sorted(known)},
    )


def result_flag_checks(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    checks: list[Dict[str, Any]] = []
    for flag, check_id, message in (
        (
            "character_validation_passed",
            "script_character_validation",
            "script character validator must pass",
        ),
        (
            "info_gate_validation_passed",
            "script_info_gate",
            "script must not reveal unrevealed information",
        ),
        (
            "transition_validation_passed",
            "script_transitions",
            "scene transitions must be plausible",
        ),
        (
            "script_quality_passed",
            "script_quality",
            "script quality validator must pass",
        ),
    ):
        if flag in result:
            checks.append(
                make_quality_check(
                    check_id, bool(result.get(flag)), message, details=result
                )
            )
    return checks


def script_quality_check(
    content: Dict[str, Any], story: Dict[str, Any], result: Dict[str, Any]
) -> Dict[str, Any] | None:
    if "script_quality_passed" in result:
        return None
    quality = ScriptQualityValidator().validate(
        content, extract_story_characters(story)
    )
    return make_quality_check(
        "script_quality",
        quality.passed,
        "script quality validator must pass",
        details=quality.to_dict(),
    )


def duration_check(result: Dict[str, Any]) -> Dict[str, Any]:
    reasoning = (
        result.get("reasoning") if isinstance(result.get("reasoning"), list) else []
    )
    duration_failed = any(
        "react_max_retries_reached" in str(item) for item in reasoning
    )
    return make_quality_check(
        "script_duration_react",
        not duration_failed,
        "duration REACT must not exhaust retries",
        details={"reasoning": reasoning},
    )


async def lint_check(
    content: Dict[str, Any],
    lint_threshold: float,
    target_chars_per_episode: Optional[int] = None,
    ai_manager: Any = None,
    model: Optional[str] = None,
    prefer_provider: Optional[str] = None,
) -> Dict[str, Any]:
    target_min = None
    target_max = None
    if target_chars_per_episode:
        target_min = max(1, int(target_chars_per_episode * 0.7))
        target_max = int(target_chars_per_episode * 1.25)
    lint_result = await lint_script_content_async(
        str(content.get("content") or ""),
        options=ScriptLintOptions(
            pass_threshold=lint_threshold,
            target_word_min=target_min,
            target_word_max=target_max,
        ),
        ai_manager=ai_manager,
        model=model,
        prefer_provider=prefer_provider,
    )
    return make_quality_check(
        "script_lint",
        lint_result.passed,
        "script lint must pass",
        score=lint_result.overall_score / 10.0,
        details=lint_result.model_dump(),
    )


def _is_generic(speaker: str, generic: set[str]) -> bool:
    return any(speaker == item or speaker.startswith(item) for item in generic)
