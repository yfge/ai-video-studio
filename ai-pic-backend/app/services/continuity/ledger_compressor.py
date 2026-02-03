"""Priority-based continuity ledger compression.

Replaces FIFO truncation with importance-based sorting to preserve
critical continuity information when compacting for prompts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass
class CompressionConfig:
    """Configuration for ledger compression limits."""

    max_facts: int = 25
    max_timeline: int = 30
    max_open_threads: int = 25
    max_resolved_threads: int = 25
    max_info_events: int = 60


# Keywords indicating high importance
IMPORTANCE_KEYWORDS_ZH = {
    "high": ["关键", "重要", "核心", "致命", "真相", "秘密", "身份", "死亡", "生死"],
    "medium": ["冲突", "转折", "悬念", "发现", "揭示", "隐藏", "证据", "线索"],
}

IMPORTANCE_KEYWORDS_EN = {
    "high": ["critical", "key", "core", "fatal", "truth", "secret", "identity", "death"],
    "medium": ["conflict", "twist", "suspense", "discovery", "reveal", "hidden", "clue"],
}

# Info types ranked by importance
INFO_TYPE_PRIORITY = {
    "identity": 10,
    "secret": 9,
    "motive": 8,
    "relationship": 7,
    "event": 5,
    "location": 4,
    "fact": 3,
}


def _score_text_importance(text: str) -> float:
    """Score a text string based on importance keywords."""
    if not text:
        return 0.0

    text_lower = text.lower()
    score = 0.0

    # Check Chinese keywords
    for kw in IMPORTANCE_KEYWORDS_ZH["high"]:
        if kw in text:
            score += 3.0
    for kw in IMPORTANCE_KEYWORDS_ZH["medium"]:
        if kw in text:
            score += 1.5

    # Check English keywords
    for kw in IMPORTANCE_KEYWORDS_EN["high"]:
        if kw in text_lower:
            score += 3.0
    for kw in IMPORTANCE_KEYWORDS_EN["medium"]:
        if kw in text_lower:
            score += 1.5

    return score


def _extract_character_names(text: str, known_characters: Set[str]) -> Set[str]:
    """Extract character names mentioned in text."""
    mentioned = set()
    for char in known_characters:
        if char and char in text:
            mentioned.add(char)
    return mentioned


def score_fact(fact: str, known_characters: Set[str]) -> float:
    """Score a fact based on importance and character involvement."""
    if not fact:
        return 0.0

    score = 1.0  # Base score

    # Importance keywords
    score += _score_text_importance(fact)

    # Character involvement bonus
    mentioned = _extract_character_names(fact, known_characters)
    score += len(mentioned) * 0.5

    # Length bonus (longer facts often contain more detail)
    if len(fact) > 50:
        score += 0.5
    if len(fact) > 100:
        score += 0.5

    return score


def score_timeline_item(
    item: Dict[str, Any],
    max_episode: int,
    known_characters: Set[str],
) -> float:
    """Score a timeline item based on recency and content richness."""
    if not isinstance(item, dict):
        return 0.0

    # Empty or meaningless items get zero score
    ep_num = item.get("episode_number", 0)
    if not ep_num and not item.get("events") and not item.get("reveals"):
        return 0.0

    score = 1.0  # Base score

    # Recency bonus: more recent episodes get higher priority
    if max_episode > 0 and ep_num > 0:
        recency_ratio = ep_num / max_episode
        score += recency_ratio * 5.0  # Up to 5 points for most recent

    # Content richness
    reveals = item.get("reveals") or []
    if isinstance(reveals, list):
        score += len(reveals) * 1.0  # Each reveal adds 1 point

    if item.get("end_state"):
        score += 2.0

    events = item.get("events") or []
    if isinstance(events, list):
        score += len(events) * 0.3

    # Important anchors
    if item.get("time_anchor"):
        score += 0.5
    if item.get("location_anchor"):
        score += 0.5

    return score


def score_thread(thread: str, known_characters: Set[str]) -> float:
    """Score a thread (open or resolved) based on importance."""
    if not thread:
        return 0.0

    score = 1.0  # Base score

    # Importance keywords
    score += _score_text_importance(thread)

    # Character involvement
    mentioned = _extract_character_names(thread, known_characters)
    score += len(mentioned) * 0.5

    # Question marks indicate unresolved tension
    if "?" in thread or "？" in thread:
        score += 1.0

    return score


def score_info_event(
    event: Dict[str, Any],
    max_episode: int,
    known_characters: Set[str],
) -> float:
    """Score an info acquisition event based on importance and recency."""
    if not isinstance(event, dict):
        return 0.0

    # Empty or meaningless events get zero score
    if not event.get("who") and not event.get("what"):
        return 0.0

    score = 1.0  # Base score
    ep_num = event.get("episode_number") or 0

    # Recency bonus
    if max_episode > 0 and ep_num > 0:
        recency_ratio = ep_num / max_episode
        score += recency_ratio * 3.0

    # Character importance
    who = event.get("who") or ""
    if who in known_characters:
        score += 2.0
    if who == "观众":
        score += 1.0  # Audience knowledge is important for dramatic irony

    # Info content importance
    what = event.get("what") or ""
    score += _score_text_importance(what)

    # How method bonus
    how = event.get("how") or ""
    if any(kw in how for kw in ["揭示", "发现", "目击", "证据"]):
        score += 1.0

    return score


def _get_max_episode(timeline: List[Dict[str, Any]]) -> int:
    """Get the maximum episode number from timeline."""
    max_ep = 0
    for item in timeline:
        if isinstance(item, dict):
            ep = item.get("episode_number", 0)
            if isinstance(ep, int) and ep > max_ep:
                max_ep = ep
    return max_ep


def _get_known_characters(characters: Dict[str, Any]) -> Set[str]:
    """Extract character names from characters dict."""
    if not isinstance(characters, dict):
        return set()
    return set(characters.keys())


def compress_ledger_by_priority(
    ledger: Dict[str, Any],
    config: Optional[CompressionConfig] = None,
) -> Dict[str, Any]:
    """Compress ledger using priority-based sorting instead of FIFO truncation.

    Args:
        ledger: The continuity ledger to compress
        config: Optional compression configuration

    Returns:
        Compressed ledger dict with most important items preserved
    """
    if config is None:
        config = CompressionConfig()

    base = ledger if isinstance(ledger, dict) else {}

    # Extract metadata for scoring
    characters = base.get("characters") if isinstance(base.get("characters"), dict) else {}
    known_chars = _get_known_characters(characters)
    timeline = base.get("timeline") if isinstance(base.get("timeline"), list) else []
    max_episode = _get_max_episode(timeline)

    # Score and sort facts
    facts_raw = base.get("facts") if isinstance(base.get("facts"), list) else []
    facts_scored = [(f, score_fact(f, known_chars)) for f in facts_raw if f]
    facts_scored.sort(key=lambda x: x[1], reverse=True)
    facts = [f for f, _ in facts_scored[: config.max_facts]]

    # Score and sort timeline items
    timeline_scored = [
        (item, score_timeline_item(item, max_episode, known_chars))
        for item in timeline
        if isinstance(item, dict)
    ]
    timeline_scored.sort(key=lambda x: x[1], reverse=True)
    timeline_compressed = [item for item, _ in timeline_scored[: config.max_timeline]]
    # Re-sort by episode number for chronological order in output
    timeline_compressed.sort(key=lambda x: x.get("episode_number", 0))

    # Score and sort open threads
    open_raw = (
        base.get("open_threads") if isinstance(base.get("open_threads"), list) else []
    )
    open_scored = [(t, score_thread(t, known_chars)) for t in open_raw if t]
    open_scored.sort(key=lambda x: x[1], reverse=True)
    open_threads = [t for t, _ in open_scored[: config.max_open_threads]]

    # Score and sort resolved threads
    resolved_raw = (
        base.get("resolved_threads")
        if isinstance(base.get("resolved_threads"), list)
        else []
    )
    resolved_scored = [(t, score_thread(t, known_chars)) for t in resolved_raw if t]
    resolved_scored.sort(key=lambda x: x[1], reverse=True)
    resolved_threads = [t for t, _ in resolved_scored[: config.max_resolved_threads]]

    # Score and sort info acquisition events
    events_raw = (
        base.get("info_acquisition_events")
        if isinstance(base.get("info_acquisition_events"), list)
        else []
    )
    events_scored = [
        (e, score_info_event(e, max_episode, known_chars))
        for e in events_raw
        if isinstance(e, dict)
    ]
    events_scored.sort(key=lambda x: x[1], reverse=True)
    events = [e for e, _ in events_scored[: config.max_info_events]]

    return {
        "version": int(base.get("version") or 1),
        "facts": facts,
        "timeline": timeline_compressed,
        "characters": characters,
        "info_acquisition_events": events,
        "open_threads": open_threads,
        "resolved_threads": resolved_threads,
    }
