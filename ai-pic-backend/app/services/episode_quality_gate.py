from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict, Optional

from pydantic import ValidationError

from app.schemas.generation import EpisodePlanItem, EpisodePlanModel
from app.services.episode.episode_generation_utils import is_episode_payload_valid
from app.services.episode.episode_scene_normalization import ensure_scenes
from app.services.episode_agent_validation import (
    validate_episode_characters,
    validate_episode_quality,
)
from app.services.narrative_context import extract_story_characters
from app.services.quality_gate_core import (
    MAX_QUALITY_GATE_REPAIRS,
    NarrativeQualityGateError,
    build_quality_gate_report,
    make_quality_check,
    quality_gate_attempt_snapshot,
)
from app.services.quality_gate_repair import repair_quality_gate_payload
from app.utils.json_utils import extract_json_block


def _episode_result_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    normalized = result.get("normalized") if isinstance(result, dict) else None
    if isinstance(normalized, dict) and isinstance(normalized.get("episodes"), list):
        return deepcopy(normalized)
    raw = result.get("content") if isinstance(result, dict) else None
    parsed = extract_json_block(raw) if isinstance(raw, str) else None
    return parsed if isinstance(parsed, dict) else {"episodes": []}


def evaluate_episode_quality_gate(
    *,
    episodes: list[Dict[str, Any]],
    story: Dict[str, Any],
    episode_count: int,
    continuity_ledger: Optional[Dict[str, Any]] = None,
    repair_attempts: Optional[list[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    checks: list[Dict[str, Any]] = [
        make_quality_check(
            "episode_non_empty", bool(episodes), "episodes must not be empty"
        ),
        make_quality_check(
            "episode_count",
            len(episodes) == episode_count,
            f"expected {episode_count} episodes, got {len(episodes)}",
            details={"expected": episode_count, "actual": len(episodes)},
        ),
    ]

    numbers = [ep.get("episode_number") for ep in episodes if isinstance(ep, dict)]
    expected_numbers = set(range(1, episode_count + 1))
    checks.append(
        make_quality_check(
            "episode_numbers",
            set(numbers) == expected_numbers and len(numbers) == len(set(numbers)),
            "episode numbers must be unique and cover the requested range",
            details={"expected": sorted(expected_numbers), "actual": numbers},
        )
    )

    schema_errors: list[str] = []
    content_errors: list[str] = []
    scene_errors: list[str] = []
    for idx, episode in enumerate(episodes, start=1):
        try:
            EpisodePlanItem.model_validate(episode)
        except ValidationError as exc:
            schema_errors.append(f"episode {idx}: {exc.errors()[:2]}")
        if not is_episode_payload_valid(episode):
            content_errors.append(f"episode {episode.get('episode_number') or idx}")
        scenes, _ = ensure_scenes(episode)
        if not scenes:
            scene_errors.append(f"episode {episode.get('episode_number') or idx}")

    checks.extend(
        [
            make_quality_check(
                "episode_schema",
                not schema_errors,
                "episode schema valid",
                details={"errors": schema_errors},
            ),
            make_quality_check(
                "episode_min_content",
                not content_errors,
                "episode minimum content valid",
                details={"errors": content_errors},
            ),
            make_quality_check(
                "episode_scenes",
                not scene_errors,
                "episodes have usable scenes",
                details={"errors": scene_errors},
            ),
        ]
    )

    story_characters = extract_story_characters(story)
    character_validation = validate_episode_characters(episodes, story_characters)
    checks.append(
        make_quality_check(
            "episode_characters",
            character_validation.get("character_validation_passed", True),
            "episode characters must match story characters",
            details=character_validation,
        )
    )

    quality_validation = validate_episode_quality(
        episodes, story_characters, continuity_ledger
    )
    checks.append(
        make_quality_check(
            "episode_quality",
            quality_validation.get("episode_quality_passed", True),
            "episode quality validator must pass",
            details=quality_validation,
        )
    )

    ledger_errors = _continuity_errors(continuity_ledger)
    checks.append(
        make_quality_check(
            "episode_continuity",
            not ledger_errors,
            "continuity ledger must not contain hard errors",
            severity="error" if ledger_errors else "info",
            details={"errors": ledger_errors},
        )
    )
    return build_quality_gate_report(
        kind="episode", checks=checks, repair_attempts=repair_attempts
    )


def _continuity_errors(continuity_ledger: Optional[Dict[str, Any]]) -> list[Any]:
    errors: list[Any] = []
    if isinstance(continuity_ledger, dict):
        for key in ("errors", "continuity_errors"):
            raw = continuity_ledger.get(key)
            if isinstance(raw, list):
                errors.extend(raw)
    return errors


async def enforce_episode_quality_gate_with_repair(
    *,
    ai_manager: Any,
    result: Dict[str, Any],
    story: Dict[str, Any],
    episode_count: int,
    model: Optional[str] = None,
    prefer_provider: Optional[str] = None,
    temperature: float = 0.3,
    max_repairs: int = MAX_QUALITY_GATE_REPAIRS,
) -> Dict[str, Any]:
    payload = _episode_result_payload(result)
    episodes = payload.get("episodes") or []
    attempts: list[Dict[str, Any]] = []
    gate = evaluate_episode_quality_gate(
        episodes=episodes,
        story=story,
        episode_count=episode_count,
        continuity_ledger=(
            result.get("continuity_ledger")
            if isinstance(result.get("continuity_ledger"), dict)
            else story.get("continuity_ledger")
        ),
    )
    if gate["passed"]:
        return _with_episode_gate(result, episodes, gate)

    for attempt in range(1, max_repairs + 1):
        repaired = await repair_quality_gate_payload(
            ai_manager=ai_manager,
            kind="episode",
            payload={"episodes": episodes},
            quality_gate=gate,
            schema={
                "name": "episode_plan",
                "schema": EpisodePlanModel.model_json_schema(),
            },
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        attempts.append(
            {
                "attempt": attempt,
                "input_gate": quality_gate_attempt_snapshot(gate),
                "repaired": bool(repaired),
            }
        )
        if not repaired:
            continue
        episodes = (
            repaired.get("episodes")
            if isinstance(repaired.get("episodes"), list)
            else []
        )
        gate = evaluate_episode_quality_gate(
            episodes=episodes,
            story=story,
            episode_count=episode_count,
            continuity_ledger=(
                result.get("continuity_ledger")
                if isinstance(result.get("continuity_ledger"), dict)
                else story.get("continuity_ledger")
            ),
            repair_attempts=deepcopy(attempts),
        )
        attempts[-1]["output_gate"] = quality_gate_attempt_snapshot(gate)
        if gate["passed"]:
            return _with_episode_gate(result, episodes, gate)

    gate["repair_attempts"] = attempts
    raise NarrativeQualityGateError("episode", gate)


def _with_episode_gate(
    result: Dict[str, Any], episodes: list[Dict[str, Any]], gate: Dict[str, Any]
) -> Dict[str, Any]:
    updated = dict(result)
    updated["normalized"] = {"episodes": episodes}
    updated["content"] = json.dumps({"episodes": episodes}, ensure_ascii=False)
    updated["quality_gate"] = gate
    return updated
