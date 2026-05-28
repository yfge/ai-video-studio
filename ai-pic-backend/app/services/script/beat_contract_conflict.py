from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_specificity import is_specific_text


def conflict_issues(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    conflict = scene.conflict

    if not conflict.question.strip() or not is_specific_text(conflict.question):
        issues.append(
            {
                "check_id": "scene_conflict_question",
                "message": "scene conflict must name a concrete dramatic question",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"question": conflict.question},
            }
        )

    if not conflict.stakes.strip() or not conflict.opposition.strip():
        issues.append(
            {
                "check_id": "scene_conflict",
                "message": "scene conflict must name stakes and opposition",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {
                    "stakes": conflict.stakes,
                    "opposition": conflict.opposition,
                },
            }
        )
    elif not is_specific_text(conflict.stakes) or not is_specific_text(
        conflict.opposition
    ):
        issues.append(
            {
                "check_id": "scene_conflict_specificity",
                "message": "scene conflict must include concrete stakes and opposition",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {
                    "stakes": conflict.stakes,
                    "opposition": conflict.opposition,
                },
            }
        )

    turn = conflict.turn or ""
    if not turn.strip() or not is_specific_text(turn):
        issues.append(
            {
                "check_id": "scene_conflict_turn",
                "message": "scene conflict must name a concrete turn",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"turn": conflict.turn},
            }
        )

    return issues
