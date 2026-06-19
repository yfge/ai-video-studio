from __future__ import annotations

from typing import Any, Dict, Optional

_EPISODE_CONTRACT_REPAIR_INSTRUCTIONS = """
For every item in episodes, include a non-empty structured_episode_contract object.
It must contain these keys with concrete production values:
episode_goal, ignition_0_3s, first_30s_reason, midpoint_jolt, payoff,
final_button_cliffhanger, visual_anchor, information_delta, dialogue_functions.
Do not move this contract into scenes, plot_points, summary, or metadata.
Preserve episode_number, title, scenes, duration, payoff, and cliffhanger while adding the missing contract.
"""


def episode_contract_repair_instructions(require_episode_contract: bool) -> str | None:
    return _EPISODE_CONTRACT_REPAIR_INSTRUCTIONS if require_episode_contract else None


def continuity_errors(continuity_ledger: Optional[Dict[str, Any]]) -> list[Any]:
    errors: list[Any] = []
    if isinstance(continuity_ledger, dict):
        for key in ("errors", "continuity_errors"):
            raw = continuity_ledger.get(key)
            if isinstance(raw, list):
                errors.extend(raw)
    return errors
