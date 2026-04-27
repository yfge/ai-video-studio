"""TTS emotion normalization helpers."""

from __future__ import annotations

from typing import Sequence

ALLOWED_TTS_EMOTIONS = {
    "happy",
    "sad",
    "angry",
    "fearful",
    "disgusted",
    "surprised",
    "calm",
    "fluent",
    "whisper",
}


def normalize_tts_emotion(
    emotion: str | None,
    *,
    action: str | None = None,
) -> str | None:
    """Normalize emotion string to allowed TTS emotion labels."""
    if not emotion and not action:
        return None

    raw = " ".join(
        v.strip()
        for v in [emotion or "", action or ""]
        if isinstance(v, str) and v.strip()
    )
    if not raw:
        return None

    raw_lower = raw.lower()

    if isinstance(emotion, str) and emotion.strip().lower() in ALLOWED_TTS_EMOTIONS:
        return emotion.strip().lower()

    def _has_any(tokens: Sequence[str]) -> bool:
        return any(tok in raw_lower for tok in tokens)

    if _has_any(
        ["whisper", "低语", "耳语", "压低", "小声", "悄声", "轻声", "低声", "自语"]
    ):
        return "whisper"
    if _has_any(["angry", "愤怒", "生气", "恼火", "怒", "火大", "暴躁"]):
        return "angry"
    if _has_any(
        [
            "sad",
            "悲伤",
            "难过",
            "沮丧",
            "哽咽",
            "哭",
            "伤心",
            "叹气",
            "叹了口气",
            "叹了一口气",
            "叹息",
            "长叹",
        ]
    ):
        return "sad"
    if _has_any(["happy", "高兴", "开心", "喜悦", "兴奋", "激动", "欢快", "愉快"]):
        return "happy"
    if _has_any(["surprised", "惊讶", "吃惊", "震惊", "惊"]):
        return "surprised"
    if _has_any(["fearful", "害怕", "恐惧", "紧张", "慌", "担心", "焦虑", "畏惧"]):
        return "fearful"
    if _has_any(["disgusted", "厌恶", "恶心", "反感"]):
        return "disgusted"
    if _has_any(
        [
            "calm",
            "neutral",
            "thoughtful",
            "平静",
            "冷静",
            "中性",
            "沉稳",
            "严肃",
            "思考",
            "克制",
        ]
    ):
        return "calm"
    if _has_any(
        [
            "fluent",
            "confident",
            "assertive",
            "自信",
            "坚定",
            "果断",
            "专业",
            "流利",
            "从容",
        ]
    ):
        return "fluent"

    return None
