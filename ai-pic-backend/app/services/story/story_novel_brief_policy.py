"""Versioned beat density for chapter planning briefs."""

import math

LEGACY_BRIEF_POLICY_VERSION = "story_novel_chapter_brief_policy.v3"
BRIEF_POLICY_VERSION = "story_novel_chapter_brief_policy.v4"


def expected_beat_count(target_chars: int, policy_version: str | None = None) -> int:
    if isinstance(target_chars, bool) or not isinstance(target_chars, int):
        raise ValueError("target_chars 必须是正整数")
    if target_chars <= 0:
        raise ValueError("target_chars 必须是正整数")
    if policy_version == LEGACY_BRIEF_POLICY_VERSION:
        return max(6, min(12, math.ceil(target_chars / 450)))
    if policy_version not in {None, BRIEF_POLICY_VERSION}:
        raise ValueError("chapter brief policy version 无效")
    return max(6, min(12, math.ceil(target_chars / 450)))
