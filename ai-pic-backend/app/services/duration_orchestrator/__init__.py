"""
Duration Orchestrator Agent

端到端时长闭环验证系统，确保从剧集到时间轴/对白到分镜的时长精确对齐。

核心功能:
1. 预算分配: 根据 total_duration_minutes 计算每个场景的时长预算和字数目标
2. 场景级闭环: 每个场景生成后立即 TTS 测量，不达标则重新生成
3. 预算再平衡: 某场景超时/欠时时动态调整后续场景预算
4. 最终验证: 确保剧集总时长在 ±10% 容差内
"""

from app.services.duration_orchestrator.agent import (
    DurationOrchestratorAgent,
    orchestrate_episode_duration,
)
from app.services.duration_orchestrator.constants import (
    BUFFER_RATIO,
    DURATION_TOLERANCE_EPISODE,
    DURATION_TOLERANCE_SCENE,
    MAX_RETRY_ATTEMPTS,
    WORDS_PER_SECOND,
)
from app.services.duration_orchestrator.state import (
    OrchestratorState,
    SceneBudget,
    SceneStatus,
)

__all__ = [
    # Agent
    "DurationOrchestratorAgent",
    "orchestrate_episode_duration",
    # State
    "OrchestratorState",
    "SceneBudget",
    "SceneStatus",
    # Constants
    "DURATION_TOLERANCE_SCENE",
    "DURATION_TOLERANCE_EPISODE",
    "MAX_RETRY_ATTEMPTS",
    "WORDS_PER_SECOND",
    "BUFFER_RATIO",
]
