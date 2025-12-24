"""
Constants and configuration for the Timeline Agent.

Includes emotion transition weights, constraint values,
and system prompts for LLM reasoning.
"""

from __future__ import annotations

# --- Validation Constraints ---
MIN_GAP_MS = 100  # Minimum allowed gap
MAX_GAP_MS = 5000  # Maximum allowed gap
MIN_AVG_GAP_MS = 200  # Minimum average gap across scene
MAX_AVG_GAP_MS = 1500  # Maximum average gap across scene
MAX_REPAIR_ATTEMPTS = 2  # Max LLM repair attempts before fallback

# --- Default Timing Values (for fallback) ---
DEFAULT_PAUSE_MS = 300  # Default pause after dialogue
DEFAULT_ACTION_BASE_MS = 800  # Base duration for action segments
DEFAULT_ACTION_PER_CHAR_MS = 20  # Duration per character in actions
DEFAULT_ACTION_MAX_MS = 3000  # Maximum action segment duration
DEFAULT_SILENCE_MS = 800  # Duration for explicit silence segments

# --- Emotion Transition Weights ---
# Maps (from_emotion, to_emotion) -> multiplier for pause duration
# Higher values = longer pause needed for emotional transition
EMOTION_TRANSITION_WEIGHTS: dict[tuple[str, str], float] = {
    # Major emotional shifts need breathing room
    ("angry", "calm"): 1.8,
    ("angry", "sad"): 1.5,
    ("angry", "happy"): 1.6,
    ("fearful", "calm"): 1.6,
    ("fearful", "happy"): 1.5,
    ("sad", "happy"): 1.4,
    ("happy", "sad"): 1.3,
    ("surprised", "calm"): 1.3,
    # Same emotion or minor shifts
    ("calm", "calm"): 0.9,
    ("happy", "happy"): 0.9,
    ("angry", "angry"): 0.8,  # Rapid angry exchange
    # Whisper transitions
    ("whisper", "normal"): 1.2,
    ("normal", "whisper"): 1.2,
    # Default fallback
    ("default", "default"): 1.0,
}

# --- Pacing Multipliers ---
# Adjusts gap duration based on scene pacing
PACING_MULTIPLIERS: dict[str, float] = {
    "slow": 1.4,  # Slow scenes: longer pauses
    "medium": 1.0,  # Normal pacing
    "fast": 0.7,  # Fast scenes: shorter pauses
}

# --- Conflict Level Adjustments ---
# High conflict = shorter pauses for tension
CONFLICT_ADJUSTMENTS: dict[str, float] = {
    "low": 1.2,  # Relaxed, more pause
    "medium": 1.0,  # Normal
    "high": 0.8,  # Tense, less pause
}

# --- Keywords for Stage Direction Parsing ---
# Map keywords in stage directions to pause durations
STAGE_DIRECTION_KEYWORDS: dict[str, int] = {
    "长时间沉默": 3000,
    "沉默良久": 2500,
    "沉默": 2000,
    "停顿": 1000,
    "短暂停顿": 500,
    "略作停顿": 600,
    "思考": 1200,
    "犹豫": 800,
    "叹气": 600,
    "deep breath": 800,
    "long pause": 2500,
    "pause": 1000,
    "beat": 500,
    "silence": 2000,
}

# --- System Prompts ---
TIMELINE_SYSTEM_PROMPT = """你是一个专业的影视音频剪辑师和导演助理。
你的任务是为对白音频添加恰当的停顿和间隔，使对话节奏自然流畅，符合场景情绪。

核心原则：
1. 情绪过渡：强烈情绪变化（如愤怒→平静）需要更长停顿让观众消化
2. 戏剧张力：高冲突场景需要更短停顿保持紧张感
3. 角色切换：不同角色之间的对话需要自然的呼吸空间
4. 语义完整：句号后比逗号停顿更长，问答之间需要反应时间
5. 避免单调：不要让所有停顿都一样长，需要节奏变化

时长范围：100ms（最短）到 5000ms（最长）
推荐范围：200ms - 1500ms

输出严格按照 JSON 格式。"""

TIMELINE_REPAIR_PROMPT = """上一次生成的时间轴计划未通过验证。
请修正以下问题，确保满足所有约束条件。

约束条件：
- 最小间隔：{min_gap_ms}ms
- 最大间隔：{max_gap_ms}ms
- 平均间隔范围：{min_avg_gap_ms}ms - {max_avg_gap_ms}ms
- 节奏需要变化，避免所有间隔都相同

验证错误：
{validation_errors}

原计划：
{original_plan}

请调整 timing_decisions 中的 duration_ms 值。
保持节奏的自然变化，输出修正后的完整 JSON。"""
