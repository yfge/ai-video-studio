from __future__ import annotations

from typing import Any, Dict

from app.services.quality_gate_core import make_quality_check

_REQUIRED_EPISODE_CONTRACT_FIELDS = (
    "episode_goal",
    "ignition_0_3s",
    "first_30s_reason",
    "midpoint_jolt",
    "payoff",
    "final_button_cliffhanger",
    "visual_anchor",
    "information_delta",
    "dialogue_functions",
)


def required_episode_contract_check(episodes: list[Dict[str, Any]]) -> Dict[str, Any]:
    missing = [
        episode.get("episode_number") or idx
        for idx, episode in enumerate(episodes, start=1)
        if not isinstance(episode.get("structured_episode_contract"), dict)
    ]
    return make_quality_check(
        "structured_episode_contract_required",
        not missing,
        "production episode generation must return structured_episode_contract for every episode",
        details={"missing_episodes": missing, "required": True},
    )


def episode_contract_quality_check(
    episodes: list[Dict[str, Any]]
) -> Dict[str, Any] | None:
    contracts = [
        episode.get("structured_episode_contract")
        for episode in episodes
        if isinstance(episode.get("structured_episode_contract"), dict)
    ]
    if not contracts:
        return None
    missing: list[Dict[str, Any]] = []
    for idx, episode in enumerate(episodes, start=1):
        contract = episode.get("structured_episode_contract")
        if not isinstance(contract, dict):
            continue
        fields = [
            field
            for field in _REQUIRED_EPISODE_CONTRACT_FIELDS
            if not _has_contract_value(contract.get(field))
        ]
        if fields:
            missing.append(
                {
                    "episode": episode.get("episode_number") or idx,
                    "missing_fields": fields,
                }
            )
    return make_quality_check(
        "structured_episode_contract",
        not missing,
        "structured_episode_contract must define hook, jolt, payoff, cliffhanger, visual anchor, and dialogue functions",
        details={"missing": missing},
    )


def _has_contract_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return value is not None
