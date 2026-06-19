from __future__ import annotations

import re
from typing import Any, Dict, List

from app.services.validators.character_consistency_validator import (
    CharacterValidationResult,
    CharacterConsistencyValidator,
    CharacterProfile,
    ValidationSeverity,
)


_GENERIC_STORY_ROLE_NAMES = {
    "客户",
    "客户代表",
    "客户方",
    "团队",
    "团队成员",
    "同事",
    "背景人",
    "竞争对手",
    "竞争对手公司",
    "董事会",
    "内鬼",
    "篡改者",
}


def _is_generic_story_role_name(name: str) -> bool:
    cleaned = re.sub(r"[（(].*?[）)]", "", name or "").strip()
    return cleaned in _GENERIC_STORY_ROLE_NAMES


def _filter_generic_unknown_names(
    validation: CharacterValidationResult,
) -> CharacterValidationResult | None:
    unknown_names = validation.details.get("unknown_names")
    if validation.severity != ValidationSeverity.WARNING or not isinstance(
        unknown_names, list
    ):
        return validation

    remaining = [
        name for name in unknown_names if not _is_generic_story_role_name(str(name))
    ]
    if not remaining:
        return None
    if len(remaining) == len(unknown_names):
        return validation
    validation.details["unknown_names"] = remaining
    validation.message = f"Found {len(remaining)} unknown character(s)"
    return validation


def _build_character_profiles(
    characters: List[Dict[str, Any]],
) -> List[CharacterProfile]:
    return [
        CharacterProfile(
            name=char.get("name", ""),
            aliases=_character_aliases(char),
            role_type=char.get("role_type") or char.get("role"),
            gender=char.get("gender"),
            age=char.get("age"),
            personality=char.get("personality", []),
            appearance=char.get("appearance") or char.get("description"),
        )
        for char in characters
        if char.get("name")
    ]


def _character_aliases(char: Dict[str, Any]) -> list[str]:
    aliases = [str(item) for item in char.get("aliases", []) if item]
    name = str(char.get("name") or "")
    if "角色" in name:
        aliases.append(re.sub(r"角色(?=[\-_—－]|$)", "", name).strip())
    return [alias for alias in aliases if alias]


def validate_story_outline_characters(
    parsed: Dict[str, Any], input_characters: List[Dict[str, Any]]
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "character_validation_passed": True,
        "character_validation_results": [],
        "character_warnings": [],
    }
    profiles = _build_character_profiles(input_characters)
    if not profiles:
        results["character_warnings"].append("No input characters to validate against")
        return results

    validator = CharacterConsistencyValidator()
    validator.register_profiles(profiles)
    for char in parsed.get("main_characters") or parsed.get("characters", []) or []:
        if not isinstance(char, dict):
            continue
        name = char.get("name") or char.get("character_name")
        if not name:
            continue
        if _is_generic_story_role_name(str(name)):
            continue
        canonical = validator.resolve_name(name)
        if not canonical:
            message = f"Generated character '{name}' not found in input characters"
            results["character_warnings"].append(message)
            results["character_validation_passed"] = False
            continue
        attrs: Dict[str, Any] = {}
        if char.get("gender"):
            attrs["gender"] = char["gender"]
        if char.get("age"):
            attrs["age"] = char["age"]
        if char.get("personality"):
            attrs["personality"] = char["personality"]
        for validation in validator.validate_character_attributes(name, attrs):
            results["character_validation_results"].append(validation.to_dict())
            if not validation.passed:
                results["character_validation_passed"] = False
                results["character_warnings"].append(validation.message)

    content_to_check = [
        text for text in (parsed.get("premise"), parsed.get("synopsis")) if text
    ]
    if content_to_check:
        for validation in validator.validate_names_in_text("\n".join(content_to_check)):
            validation = _filter_generic_unknown_names(validation)
            if validation is None:
                continue
            results["character_validation_results"].append(validation.to_dict())
            if validation.severity.value == "warning":
                results["character_warnings"].append(validation.message)
    return results


def story_outline_validation_passed(
    char_validation: Dict[str, Any], quality_validation: Dict[str, Any]
) -> bool:
    return bool(
        char_validation.get("character_validation_passed", False)
        and quality_validation.get("story_quality_passed", False)
    )
