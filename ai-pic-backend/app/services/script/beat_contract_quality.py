from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import StructuredScriptContract
from app.services.script.beat_contract_cliffhanger import cliffhanger_issues
from app.services.script.beat_contract_conflict import conflict_issues
from app.services.script.beat_contract_dialogue import dialogue_issues
from app.services.script.beat_contract_duration import duration_issues
from app.services.script.beat_contract_progression import progression_issues
from app.services.script.beat_contract_purpose import purpose_issues
from app.services.script.beat_contract_specificity import (
    character_specificity_issues,
    has_specific_payoff,
    is_payoff_beat,
    is_specific_text,
    protagonist_screen_presence_issues,
)


def evaluate_beat_contract_quality(
    contract: StructuredScriptContract,
    *,
    min_beats_per_scene: int = 3,
    max_dialogue_chars: int = 24,
    allow_ultra_short_smoke: bool = False,
) -> dict[str, Any]:
    failed: list[dict[str, Any]] = []
    required_beats = 1 if allow_ultra_short_smoke else min_beats_per_scene

    if (contract.model_extra or {}).get("fallback_detected"):
        failed.append(_failure("fallback_content", "fallback narration cannot pass"))

    for scene in contract.scenes:
        if len(scene.beats) < required_beats:
            failed.append(
                _failure(
                    "scene_min_beats",
                    "scene must contain enough beats",
                    scene_number=scene.scene_number,
                    evidence={
                        "beat_count": len(scene.beats),
                        "minimum": required_beats,
                    },
                )
            )
        _check_scene_structure(scene, failed, max_dialogue_chars)

    first_scene = contract.scenes[0]
    first_beat = first_scene.beats[0]
    if first_beat.beat_type != "hook":
        failed.append(
            _failure(
                "opening_hook_required",
                "first beat of first scene must be a hook",
                scene_number=first_scene.scene_number,
                beat_order_index=first_beat.order_index,
            )
        )
    if not _has_escalation(contract):
        failed.append(_failure("escalation_required", "script must escalate conflict"))
    if not _has_payoff(contract):
        failed.append(_failure("payoff_required", "script needs payoff"))
    final_scene = contract.scenes[-1]
    final_beat = final_scene.beats[-1]
    if final_beat.beat_type != "cliffhanger" and not final_beat.cliffhanger_tag:
        failed.append(
            _failure(
                "cliffhanger_required",
                "final beat must remain unresolved",
                scene_number=final_scene.scene_number,
                beat_order_index=final_beat.order_index,
            )
        )

    return {
        "kind": "script_beat_contract",
        "passed": not failed,
        "failed_checks": failed,
        "check_count": 24,
    }


def _check_scene_structure(
    scene, failed: list[dict[str, Any]], max_dialogue_chars: int
) -> None:
    order_indexes = [beat.order_index for beat in scene.beats]
    expected = list(range(1, len(order_indexes) + 1))
    if order_indexes != expected:
        failed.append(
            _failure(
                "beat_order",
                "beat order indexes must be contiguous",
                scene_number=scene.scene_number,
                evidence={"order_indexes": order_indexes, "expected": expected},
            )
        )
    failed.extend(conflict_issues(scene))
    if not any(beat.action_lines for beat in scene.beats):
        failed.append(
            _failure(
                "scene_action_coverage",
                "scene must include action lines",
                scene_number=scene.scene_number,
            )
        )
    if not any(beat.dialogue_lines for beat in scene.beats):
        failed.append(
            _failure(
                "scene_dialogue_coverage",
                "scene must include dialogue lines",
                scene_number=scene.scene_number,
            )
        )
    failed.extend(duration_issues(scene))
    failed.extend(progression_issues(scene))
    failed.extend(purpose_issues(scene))
    failed.extend(character_specificity_issues(scene))
    failed.extend(protagonist_screen_presence_issues(scene))
    failed.extend(dialogue_issues(scene))
    for beat in scene.beats:
        if not beat.visible_event.strip():
            failed.append(
                _failure(
                    "beat_visible_event",
                    "beat must include a visible event",
                    scene_number=scene.scene_number,
                    beat_order_index=beat.order_index,
                )
            )
        elif not is_specific_text(beat.visible_event):
            failed.append(
                _failure(
                    "beat_visible_event_specificity",
                    "beat visible event must be concrete and filmable",
                    scene_number=scene.scene_number,
                    beat_order_index=beat.order_index,
                    evidence={"visible_event": beat.visible_event},
                )
            )
        if beat.action_lines and not any(
            is_specific_text(action.content) for action in beat.action_lines
        ):
            failed.append(
                _failure(
                    "beat_action_specificity",
                    "beat action lines must name concrete screen behavior",
                    scene_number=scene.scene_number,
                    beat_order_index=beat.order_index,
                    evidence={
                        "action_lines": [action.content for action in beat.action_lines]
                    },
                )
            )
        if is_payoff_beat(beat) and not has_specific_payoff(beat):
            failed.append(
                _failure(
                    "payoff_specificity",
                    "payoff beat must show a concrete result",
                    scene_number=scene.scene_number,
                    beat_order_index=beat.order_index,
                    evidence={
                        "visible_event": beat.visible_event,
                        "payoff_tag": beat.payoff_tag,
                    },
                )
            )
        for line in beat.dialogue_lines:
            if _visible_len(line.content) > max_dialogue_chars:
                failed.append(
                    _failure(
                        "dialogue_line_length",
                        "dialogue line exceeds short-drama limit",
                        scene_number=scene.scene_number,
                        beat_order_index=beat.order_index,
                        evidence={"content": line.content},
                    )
                )
    failed.extend(cliffhanger_issues(scene.beats[-1], scene.scene_number))


def _has_escalation(contract: StructuredScriptContract) -> bool:
    return any(
        scene.dramatic_role == "escalation"
        or any(beat.beat_type in {"conflict", "reveal"} for beat in scene.beats)
        for scene in contract.scenes
    )


def _has_payoff(contract: StructuredScriptContract) -> bool:
    return any(
        scene.dramatic_role == "payoff"
        or any(is_payoff_beat(beat) for beat in scene.beats)
        for scene in contract.scenes
    )


def _failure(
    check_id: str,
    message: str,
    *,
    scene_number: int | None = None,
    beat_order_index: int | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "message": message,
        "scene_number": scene_number,
        "beat_order_index": beat_order_index,
        "evidence": evidence or {},
    }


def _visible_len(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))
