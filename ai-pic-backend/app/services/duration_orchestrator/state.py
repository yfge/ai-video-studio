"""
Duration Orchestrator 状态定义

定义 LangGraph StateGraph 所需的状态数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SceneStatus(str, Enum):
    """场景生成状态"""

    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 处理中
    COMMITTED = "committed"  # 已提交（验证通过）
    FAILED = "failed"  # 失败（达到最大重试次数）


@dataclass
class SceneBudget:
    """单个场景的时长预算"""

    # 基础标识
    scene_number: int
    scene_index: int  # 在场景列表中的索引 (0-based)

    # 时长目标
    target_duration_seconds: int
    target_word_count: int  # 目标对白字数

    # 容差范围
    min_duration_seconds: int  # 最小可接受时长 (target * 0.85)
    max_duration_seconds: int  # 最大可接受时长 (target * 1.15)

    # 运行时状态
    status: SceneStatus = SceneStatus.PENDING
    attempt_count: int = 0

    # 实际结果
    actual_duration_seconds: Optional[float] = None
    actual_word_count: Optional[int] = None
    actual_dialogue_count: Optional[int] = None

    # 失败/重试信息
    last_rejection_reason: Optional[str] = None
    adjustment_hint: Optional[str] = None

    # 生成结果引用
    script_scene_data: Optional[Dict[str, Any]] = None
    tts_results: Optional[List[Dict[str, Any]]] = None
    scene_beats: Optional[List[Dict[str, Any]]] = None

    def is_within_tolerance(self) -> bool:
        """检查实际时长是否在容差范围内"""
        if self.actual_duration_seconds is None:
            return False
        return (
            self.min_duration_seconds
            <= self.actual_duration_seconds
            <= self.max_duration_seconds
        )

    def duration_ratio(self) -> Optional[float]:
        """计算实际时长与目标时长的比例"""
        if self.actual_duration_seconds is None or self.target_duration_seconds == 0:
            return None
        return self.actual_duration_seconds / self.target_duration_seconds

    def duration_diff_seconds(self) -> Optional[float]:
        """计算时长差异 (秒)，正数表示超时，负数表示不足"""
        if self.actual_duration_seconds is None:
            return None
        return self.actual_duration_seconds - self.target_duration_seconds

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scene_number": self.scene_number,
            "scene_index": self.scene_index,
            "target_duration_seconds": self.target_duration_seconds,
            "target_word_count": self.target_word_count,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "actual_duration_seconds": self.actual_duration_seconds,
            "actual_word_count": self.actual_word_count,
            "actual_dialogue_count": self.actual_dialogue_count,
            "last_rejection_reason": self.last_rejection_reason,
            "adjustment_hint": self.adjustment_hint,
            "is_within_tolerance": self.is_within_tolerance(),
            "duration_ratio": self.duration_ratio(),
        }


@dataclass
class OrchestratorState:
    """Duration Orchestrator 的全局状态"""

    # ==========================================================================
    # 输入参数
    # ==========================================================================
    episode_id: int
    script_id: int
    story_id: int
    total_duration_minutes: int

    # Episode Agent 产出的场景列表 (原始数据)
    scenes_from_episode: List[Dict[str, Any]] = field(default_factory=list)

    # ==========================================================================
    # 预算分配结果
    # ==========================================================================
    scene_budgets: List[SceneBudget] = field(default_factory=list)
    buffer_seconds: int = 0  # 预留 buffer

    # ==========================================================================
    # 场景生成结果
    # ==========================================================================
    committed_scenes: List[Dict[str, Any]] = field(default_factory=list)

    # ==========================================================================
    # 时长跟踪
    # ==========================================================================
    committed_duration_seconds: float = 0.0
    remaining_budget_seconds: float = 0.0

    # ==========================================================================
    # 流程控制
    # ==========================================================================
    current_scene_index: int = 0
    phase: str = (
        "init"  # init | allocating | generating | assembling | validating | done | failed
    )

    # ==========================================================================
    # 最终结果
    # ==========================================================================
    final_duration_seconds: Optional[float] = None
    final_duration_ratio: Optional[float] = None
    audio_timeline_url: Optional[str] = None
    storyboard_frames_count: int = 0

    # ==========================================================================
    # 推理日志
    # ==========================================================================
    reasoning: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # ==========================================================================
    # 辅助方法
    # ==========================================================================

    def get_current_budget(self) -> Optional[SceneBudget]:
        """获取当前正在处理的场景预算"""
        if 0 <= self.current_scene_index < len(self.scene_budgets):
            return self.scene_budgets[self.current_scene_index]
        return None

    def get_pending_budgets(self) -> List[SceneBudget]:
        """获取所有待处理的场景预算"""
        return [b for b in self.scene_budgets if b.status == SceneStatus.PENDING]

    def get_committed_budgets(self) -> List[SceneBudget]:
        """获取所有已提交的场景预算"""
        return [b for b in self.scene_budgets if b.status == SceneStatus.COMMITTED]

    def get_failed_budgets(self) -> List[SceneBudget]:
        """获取所有失败的场景预算"""
        return [b for b in self.scene_budgets if b.status == SceneStatus.FAILED]

    def all_scenes_processed(self) -> bool:
        """检查是否所有场景都已处理完成"""
        return all(
            b.status in (SceneStatus.COMMITTED, SceneStatus.FAILED)
            for b in self.scene_budgets
        )

    def total_target_duration(self) -> int:
        """计算所有场景的目标时长总和"""
        return sum(b.target_duration_seconds for b in self.scene_budgets)

    def total_actual_duration(self) -> float:
        """计算所有已提交场景的实际时长总和"""
        return sum(
            b.actual_duration_seconds or 0
            for b in self.scene_budgets
            if b.status == SceneStatus.COMMITTED
        )

    def total_retry_count(self) -> int:
        """计算总重试次数"""
        return sum(max(0, b.attempt_count - 1) for b in self.scene_budgets)

    def add_reasoning(self, msg: str) -> None:
        """添加推理日志"""
        self.reasoning.append(msg)

    def add_error(self, msg: str) -> None:
        """添加错误日志"""
        self.errors.append(msg)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 (用于持久化和日志)"""
        return {
            "episode_id": self.episode_id,
            "script_id": self.script_id,
            "story_id": self.story_id,
            "total_duration_minutes": self.total_duration_minutes,
            "scene_count": len(self.scene_budgets),
            "buffer_seconds": self.buffer_seconds,
            "phase": self.phase,
            "current_scene_index": self.current_scene_index,
            "committed_duration_seconds": self.committed_duration_seconds,
            "remaining_budget_seconds": self.remaining_budget_seconds,
            "scene_budgets": [b.to_dict() for b in self.scene_budgets],
            "committed_scenes_count": len(self.committed_scenes),
            "final_duration_seconds": self.final_duration_seconds,
            "final_duration_ratio": self.final_duration_ratio,
            "total_retry_count": self.total_retry_count(),
            "errors": self.errors,
        }

    def summary(self) -> Dict[str, Any]:
        """生成状态摘要"""
        committed = self.get_committed_budgets()
        failed = self.get_failed_budgets()
        pending = self.get_pending_budgets()

        return {
            "phase": self.phase,
            "total_scenes": len(self.scene_budgets),
            "committed": len(committed),
            "failed": len(failed),
            "pending": len(pending),
            "current_scene": self.current_scene_index + 1 if self.scene_budgets else 0,
            "committed_duration_seconds": round(self.committed_duration_seconds, 1),
            "target_duration_seconds": self.total_duration_minutes * 60,
            "progress_ratio": (
                round(len(committed) / len(self.scene_budgets), 2)
                if self.scene_budgets
                else 0
            ),
        }
