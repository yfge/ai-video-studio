"""
Utility functions for the Timeline Agent.

Provides helpers for emotion analysis, context extraction,
cache key generation, and fallback timing calculation.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Optional, Sequence

from .constants import (
    CONFLICT_ADJUSTMENTS,
    DEFAULT_PAUSE_MS,
    EMOTION_TRANSITION_WEIGHTS,
    PACING_MULTIPLIERS,
    STAGE_DIRECTION_KEYWORDS,
)
from .schemas import DialogueContext, SceneContext, TimingDecision


def compute_timing_cache_key(
    scene_id: int,
    dialogues: Sequence[dict[str, Any]],
    stage_directions: Sequence[dict[str, Any]],
) -> str:
    """
    Compute cache key for timing decisions.

    Returns MD5 hash of scene content for cache lookup.
    """
    content = json.dumps(
        {
            "scene_id": scene_id,
            "dialogues": list(dialogues),
            "stage_directions": list(stage_directions),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def extract_dominant_mood(dialogues: Sequence[dict[str, Any]]) -> Optional[str]:
    """
    Extract dominant emotional mood from dialogue emotions.

    Returns the most common emotion or None if no emotions tagged.
    """
    emotions = [
        d.get("emotion")
        for d in dialogues
        if isinstance(d.get("emotion"), str) and d.get("emotion").strip()
    ]
    if not emotions:
        return None
    counter = Counter(emotions)
    return counter.most_common(1)[0][0]


def infer_conflict_level(conflict_notes: Optional[str]) -> str:
    """
    Infer conflict level from scene conflict notes.

    Returns: 'low', 'medium', or 'high'
    """
    if not conflict_notes:
        return "medium"

    text = str(conflict_notes).lower()

    high_keywords = ["激烈", "紧张", "对峙", "高潮", "冲突", "对抗", "争吵", "争执"]
    low_keywords = ["平静", "温馨", "日常", "轻松", "和谐", "安宁"]

    for kw in high_keywords:
        if kw in text:
            return "high"
    for kw in low_keywords:
        if kw in text:
            return "low"

    return "medium"


def infer_pacing(dialogue_count: int) -> str:
    """
    Infer scene pacing from dialogue density.

    Returns: 'slow', 'medium', or 'fast'
    """
    if dialogue_count > 10:
        return "fast"
    if dialogue_count < 4:
        return "slow"
    return "medium"


def build_dialogue_contexts(
    dialogues: Sequence[dict[str, Any]],
) -> list[DialogueContext]:
    """
    Build DialogueContext list with emotion transitions.

    Extracts previous/next emotions for each dialogue.
    """
    contexts = []
    n = len(dialogues)

    for idx, dlg in enumerate(dialogues):
        prev_em = dialogues[idx - 1].get("emotion") if idx > 0 else None
        next_em = dialogues[idx + 1].get("emotion") if idx < n - 1 else None

        contexts.append(
            DialogueContext(
                index=idx,
                speaker=str(dlg.get("character") or "旁白"),
                content=str(dlg.get("content") or ""),
                emotion=dlg.get("emotion") if isinstance(dlg.get("emotion"), str) else None,
                action=dlg.get("action") if isinstance(dlg.get("action"), str) else None,
                prev_emotion=prev_em if isinstance(prev_em, str) else None,
                next_emotion=next_em if isinstance(next_em, str) else None,
                is_first=idx == 0,
                is_last=idx == n - 1,
            )
        )

    return contexts


def build_scene_context(
    scene_id: int,
    scene_number: int,
    dialogues: Sequence[dict[str, Any]],
    conflict_notes: Optional[str] = None,
    dramatic_question: Optional[str] = None,
    slug_line: Optional[str] = None,
    location: Optional[str] = None,
    time_of_day: Optional[str] = None,
    summary: Optional[str] = None,
    primary_characters: Optional[list] = None,
) -> SceneContext:
    """
    Build SceneContext from scene data.

    Extracts mood, conflict level, pacing from dialogue content and scene metadata.
    """
    mood = extract_dominant_mood(dialogues)
    conflict_level = infer_conflict_level(conflict_notes)
    pacing = infer_pacing(len(dialogues))

    # Extract characters from dialogues
    dialogue_characters = set(
        str(d.get("character") or "").strip()
        for d in dialogues
        if d.get("character")
    )

    # Merge with primary_characters if available
    all_characters = dialogue_characters
    if primary_characters and isinstance(primary_characters, list):
        for char in primary_characters:
            if isinstance(char, str):
                all_characters.add(char.strip())
            elif isinstance(char, dict) and char.get("name"):
                all_characters.add(str(char["name"]).strip())

    return SceneContext(
        scene_number=scene_number,
        scene_id=scene_id,
        mood=mood,
        conflict_level=conflict_level,
        pacing=pacing,
        character_count=max(1, len(all_characters)),
        dialogue_count=len(dialogues),
        has_dramatic_question=bool(dramatic_question),
        slug_line=slug_line,
        location=location,
        time_of_day=time_of_day,
        summary=summary,
    )


def get_emotion_transition_weight(
    from_emotion: Optional[str],
    to_emotion: Optional[str],
) -> float:
    """
    Get timing multiplier for emotion transition.

    Returns weight factor for pause duration between emotions.
    """
    key = (
        from_emotion or "default",
        to_emotion or "default",
    )

    if key in EMOTION_TRANSITION_WEIGHTS:
        return EMOTION_TRANSITION_WEIGHTS[key]

    # Try with normalized emotions
    normalized_key = (
        _normalize_emotion(from_emotion),
        _normalize_emotion(to_emotion),
    )
    if normalized_key in EMOTION_TRANSITION_WEIGHTS:
        return EMOTION_TRANSITION_WEIGHTS[normalized_key]

    return 1.0


def _normalize_emotion(emotion: Optional[str]) -> str:
    """Normalize emotion string to standard form."""
    if not emotion:
        return "default"

    emotion = emotion.lower().strip()

    # Map Chinese emotions to standard
    mapping = {
        "高兴": "happy",
        "开心": "happy",
        "喜悦": "happy",
        "悲伤": "sad",
        "难过": "sad",
        "愤怒": "angry",
        "生气": "angry",
        "恐惧": "fearful",
        "害怕": "fearful",
        "惊讶": "surprised",
        "平静": "calm",
        "低语": "whisper",
        "耳语": "whisper",
    }

    return mapping.get(emotion, emotion)


def extract_stage_direction_pause(content: str) -> Optional[int]:
    """
    Extract pause duration hint from stage direction content.

    Returns duration in ms if keyword found, else None.
    """
    if not content:
        return None

    text = content.lower().strip()

    for keyword, duration in STAGE_DIRECTION_KEYWORDS.items():
        if keyword.lower() in text:
            return duration

    return None


def calculate_fallback_timing(
    dialogue_contexts: list[DialogueContext],
    scene_context: SceneContext,
) -> list[TimingDecision]:
    """
    Calculate timing using rule-based fallback (no LLM).

    Uses emotion weights, pacing, and conflict adjustments.
    """
    base_gap = DEFAULT_PAUSE_MS
    pacing_factor = PACING_MULTIPLIERS.get(scene_context.pacing, 1.0)
    conflict_factor = CONFLICT_ADJUSTMENTS.get(scene_context.conflict_level, 1.0)

    decisions = []

    for ctx in dialogue_contexts:
        # Emotion transition factor
        emotion_factor = get_emotion_transition_weight(
            ctx.prev_emotion, ctx.emotion
        )

        # Calculate adjusted duration
        adjusted = int(base_gap * emotion_factor * pacing_factor * conflict_factor)

        # Clamp to valid range
        adjusted = max(100, min(5000, adjusted))

        decisions.append(
            TimingDecision(
                segment_index=ctx.index,
                gap_type="post_dialogue",
                base_duration_ms=base_gap,
                adjusted_duration_ms=adjusted,
                reasoning=f"fallback: emotion={emotion_factor:.2f}, pacing={pacing_factor:.2f}",
                emotion_factor=emotion_factor,
                pacing_factor=pacing_factor * conflict_factor,
            )
        )

    return decisions


def calculate_rhythm_score(decisions: list[TimingDecision]) -> float:
    """
    Calculate rhythm variety score (0-1).

    Higher score = more varied timing, 0 = monotonous.
    """
    if len(decisions) <= 1:
        return 0.5

    durations = [d.adjusted_duration_ms for d in decisions]
    mean = sum(durations) / len(durations)

    if mean == 0:
        return 0.0

    # Calculate coefficient of variation
    variance = sum((d - mean) ** 2 for d in durations) / len(durations)
    std_dev = variance ** 0.5
    cv = std_dev / mean

    # Normalize: CV of 0.3-0.5 is ideal
    # Below 0.1 is too monotonous, above 0.8 is too chaotic
    if cv < 0.1:
        return cv * 3  # Scale up low variance
    if cv > 0.8:
        return max(0.5, 1.0 - (cv - 0.8))  # Penalize extreme variance
    return min(1.0, cv * 1.5)


def format_dialogue_for_prompt(contexts: list[DialogueContext]) -> str:
    """
    Format dialogue contexts for LLM prompt.

    Returns formatted string with indices and metadata.
    """
    lines = []
    for ctx in contexts:
        emotion_str = ctx.emotion or "无标注"
        action_str = f"（{ctx.action}）" if ctx.action else ""
        prev_str = f"前一句情绪: {ctx.prev_emotion}" if ctx.prev_emotion else ""

        lines.append(
            f"[{ctx.index + 1}] {ctx.speaker}: \"{ctx.content}\" {action_str}\n"
            f"  - 情绪: {emotion_str}\n"
            f"  - {prev_str}" if prev_str else ""
        )

    return "\n".join(filter(None, lines))
