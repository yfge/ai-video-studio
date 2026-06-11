from __future__ import annotations

from typing import Any, Dict, List

from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
)


def _build_character_profiles(
    characters: List[Dict[str, Any]],
) -> List[CharacterProfile]:
    return [
        CharacterProfile(
            name=char.get("name", ""),
            aliases=char.get("aliases", []),
            role_type=char.get("role_type") or char.get("role"),
            gender=char.get("gender"),
            age=char.get("age"),
            personality=char.get("personality", []),
            appearance=char.get("appearance") or char.get("description"),
        )
        for char in characters
        if char.get("name")
    ]


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
