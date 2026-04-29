from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
)
from app.services.validators.episode_quality_validator import EpisodeQualityValidator


def build_character_profiles(
    characters: List[Dict[str, Any]],
) -> List[CharacterProfile]:
    profiles = []
    for char in characters:
        if not char.get("name"):
            continue
        profiles.append(
            CharacterProfile(
                name=char.get("name", ""),
                aliases=char.get("aliases", []),
                role_type=char.get("role_type") or char.get("role"),
                gender=char.get("gender"),
                age=char.get("age"),
                personality=char.get("personality", []),
                appearance=char.get("appearance") or char.get("description"),
            )
        )
    return profiles


def validate_episode_characters(
    episodes: List[Dict[str, Any]],
    story_characters: List[Dict[str, Any]],
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "character_validation_passed": True,
        "character_validation_results": [],
        "character_warnings": [],
    }

    profiles = build_character_profiles(story_characters)
    if not profiles:
        results["character_warnings"].append("No story characters to validate against")
        return results

    validator = CharacterConsistencyValidator()
    validator.register_profiles(profiles)

    for episode in episodes:
        ep_num = episode.get("episode_number", "?")
        content_to_check = []
        if episode.get("summary"):
            content_to_check.append(episode["summary"])
        if episode.get("description"):
            content_to_check.append(episode["description"])
        if episode.get("plot_points"):
            content_to_check.extend(str(p) for p in episode["plot_points"] if p)

        if content_to_check:
            text_results = validator.validate_names_in_text("\n".join(content_to_check))
            for result in text_results:
                result_dict = result.to_dict()
                result_dict["episode_number"] = ep_num
                results["character_validation_results"].append(result_dict)
                if result.severity.value == "warning":
                    results["character_warnings"].append(
                        f"Episode {ep_num}: {result.message}"
                    )

        ep_chars = episode.get("characters", [])
        if isinstance(ep_chars, list):
            for char in ep_chars:
                if not isinstance(char, dict):
                    continue
                name = char.get("name") or char.get("character_name")
                if not name:
                    continue
                if not validator.resolve_name(name):
                    results["character_warnings"].append(
                        f"Episode {ep_num}: Unknown character '{name}'"
                    )
                    results["character_validation_passed"] = False

    return results


def validate_episode_quality(
    episodes: List[Dict[str, Any]],
    story_characters: List[Dict[str, Any]],
    continuity_ledger: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "episode_quality_passed": True,
        "episode_quality_result": {},
        "episode_quality_warnings": [],
    }

    quality_result = EpisodeQualityValidator().validate(
        episodes, story_characters, continuity_ledger
    )
    results["episode_quality_passed"] = quality_result.passed
    results["episode_quality_result"] = quality_result.to_dict()

    for issue in quality_result.issues:
        if issue.severity.value in ("error", "warning"):
            results["episode_quality_warnings"].append(issue.message)

    return results
