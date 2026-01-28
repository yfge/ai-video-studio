from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from app.schemas.context_pack import ContextPackBudget


def _compact_json_size(value: Any) -> int:
    try:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        return len(str(value))


def truncate_text(value: Any, max_chars: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def apply_story_pack_budget(
    pack: Dict[str, Any], budget: ContextPackBudget
) -> Tuple[Dict[str, Any], List[str]]:
    """Best-effort shrinking for StoryContextPack dumps (char-based)."""
    trims: list[str] = []

    def size() -> int:
        return _compact_json_size(pack)

    # 1) Limit list sizes (already enforced by builder, but keep defensive).
    recent = pack.get("recent_episodes")
    if isinstance(recent, list) and len(recent) > budget.max_recent_episode_summaries:
        pack["recent_episodes"] = recent[: budget.max_recent_episode_summaries]
        trims.append("recent_episodes:cap")

    cards = pack.get("character_cards")
    if isinstance(cards, list) and len(cards) > budget.max_character_cards:
        pack["character_cards"] = cards[: budget.max_character_cards]
        trims.append("character_cards:cap")

    if size() <= budget.max_total_chars:
        return pack, trims

    # 2) Drop heavyweight optional fields on character cards.
    if isinstance(pack.get("character_cards"), list):
        for card in pack["character_cards"]:
            if isinstance(card, dict):
                for key in ("biography", "background_story", "voice_config"):
                    if card.get(key) is not None:
                        card[key] = None
        trims.append("character_cards:drop_heavy_fields")
    if size() <= budget.max_total_chars:
        return pack, trims

    # 3) Reduce recent episodes count more aggressively.
    if isinstance(pack.get("recent_episodes"), list) and pack["recent_episodes"]:
        pack["recent_episodes"] = pack["recent_episodes"][:1]
        trims.append("recent_episodes:keep_1")
    if size() <= budget.max_total_chars:
        return pack, trims

    # 4) Drop continuity ledger (can be large).
    if pack.get("continuity_ledger") is not None:
        pack["continuity_ledger"] = None
        trims.append("continuity_ledger:drop")
    if size() <= budget.max_total_chars:
        return pack, trims

    # 5) Truncate core text fields further.
    outline = pack.get("outline")
    if isinstance(outline, dict):
        for key in ("premise", "synopsis", "main_conflict", "resolution"):
            outline[key] = truncate_text(
                outline.get(key), max(200, budget.max_field_chars // 2)
            )
        trims.append("outline:extra_truncate")

    setting = pack.get("setting")
    if isinstance(setting, dict):
        setting["world_building"] = truncate_text(
            setting.get("world_building"), max(200, budget.max_field_chars // 2)
        )
        trims.append("setting.world_building:extra_truncate")

    # If still too large, drop relationships.
    if size() > budget.max_total_chars and pack.get("character_relationships"):
        pack["character_relationships"] = {}
        trims.append("character_relationships:drop")

    return pack, trims
