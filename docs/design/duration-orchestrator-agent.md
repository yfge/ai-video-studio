# Duration Orchestrator Agent 设计文档

> **目标**：构建端到端闭环验证系统，确保从剧集到时间轴/对白到分镜的时长精确对齐。

## 1. 问题回顾

### 1.1 当前架构的断层

```
Episode Agent                     Script Agent                    TTS Generation
     │                                 │                               │
     │ estimated_duration_seconds      │ dialogues (无时长约束)         │ actual_duration_ms
     │ (LLM 估算，误差大)               │                               │ (才知道真实时长)
     ▼                                 ▼                               ▼
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ 场景时长  │ ──❌断层1──────▶ │ 对白生成  │ ──❌断层2──────▶ │ GAP 计算  │
│ ±15%容差 │                    │ 无字数锚定│                    │ 无法拯救  │
└──────────┘                    └──────────┘                    └──────────┘
```

### 1.2 核心问题

| 问题 | 根因 | 影响 |
|------|------|------|
| **估算偏差** | `estimated_duration_seconds` 是 LLM 猜测 | 与 TTS 实际时长差异可达 50%+ |
| **无字数锚定** | Script Agent 不知道目标时长 | 对白长度随机，无法控制 |
| **单向流动** | 错误无法自我修正 | 偏差累积，最终分镜时长混乱 |
| **GAP 补救有限** | 停顿只能在 100ms~5000ms 范围 | 对白太短时无法补齐 |

## 2. 方案 C 架构设计

### 2.1 核心思想

**场景级闭环验证**：每个场景生成后立即测量，不达标则重新生成，达标后锁定。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Duration Orchestrator Agent                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Episode Budget Allocation                                           │ │
│  │    - 根据 total_duration_minutes 分配每个场景的时长预算                  │ │
│  │    - 预留 5% buffer 用于场景间过渡                                      │ │
│  │    - 计算每个场景的 target_word_count (字数目标)                         │ │
│  └─────────────────────────────┬──────────────────────────────────────────┘ │
│                                ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 2. Scene Generation Loop (per scene, max 3 attempts)                   │ │
│  │                                                                        │ │
│  │    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐ │ │
│  │    │ Script Gen │ ─▶ │ TTS Trial  │ ─▶ │ Duration   │ ─▶ │ Commit   │ │ │
│  │    │ (with word │    │ (快速估算)  │    │ Check      │    │ or Retry │ │ │
│  │    │  target)   │    │            │    │            │    │          │ │ │
│  │    └────────────┘    └────────────┘    └─────┬──────┘    └──────────┘ │ │
│  │           ▲                                  │                         │ │
│  │           │  ❌ 不达标 (提供调整建议)          │ ✅ 达标                 │ │
│  │           └──────────────────────────────────┘                         │ │
│  │                                                                        │ │
│  └─────────────────────────────┬──────────────────────────────────────────┘ │
│                                ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 3. Budget Rebalance (可选)                                             │ │
│  │    - 如果某场景超时，从后续场景预算中扣除                                 │ │
│  │    - 如果某场景欠时，将富余分配给后续场景                                 │ │
│  └─────────────────────────────┬──────────────────────────────────────────┘ │
│                                ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 4. Final Assembly                                                      │ │
│  │    - 合并所有场景的 SceneBeat                                          │ │
│  │    - 构建 Episode Audio Timeline                                       │ │
│  │    - 生成分镜帧                                                        │ │
│  │    - 验证总时长 ±10%                                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 LangGraph 状态机设计

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class SceneStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    FAILED = "failed"

@dataclass
class SceneBudget:
    """单个场景的时长预算"""
    scene_number: int
    target_duration_seconds: int
    target_word_count: int          # 目标对白字数
    min_duration_seconds: int       # 最小可接受时长 (target * 0.85)
    max_duration_seconds: int       # 最大可接受时长 (target * 1.15)

    # 运行时状态
    status: SceneStatus = SceneStatus.PENDING
    attempt_count: int = 0
    actual_duration_seconds: Optional[float] = None
    actual_word_count: Optional[int] = None

    # 失败原因 (用于 REACT 重试)
    last_rejection_reason: Optional[str] = None
    adjustment_hint: Optional[str] = None

@dataclass
class OrchestratorState:
    """Duration Orchestrator 的全局状态"""

    # 输入
    episode_id: int
    total_duration_minutes: int
    scenes_from_episode: List[Dict[str, Any]]  # Episode Agent 产出的场景列表

    # 预算分配
    scene_budgets: List[SceneBudget] = field(default_factory=list)
    buffer_seconds: int = 0  # 预留 buffer

    # 场景生成结果
    committed_scenes: List[Dict[str, Any]] = field(default_factory=list)

    # 累计时长跟踪
    committed_duration_seconds: float = 0.0
    remaining_budget_seconds: float = 0.0

    # 当前处理的场景
    current_scene_index: int = 0

    # 最终结果
    final_duration_seconds: Optional[float] = None
    final_duration_ratio: Optional[float] = None

    # 推理日志
    reasoning: List[str] = field(default_factory=list)
```

### 2.3 节点定义

```
┌─────────────────────────────────────────────────────────────────┐
│                    StateGraph Nodes                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │ allocate_   │  根据场景数量和重要性分配时长预算               │
│  │ budget      │  计算每个场景的 target_word_count               │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ select_     │  选择下一个待处理的场景                         │
│  │ next_scene  │  检查是否所有场景已完成                         │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ generate_   │  调用 Script Agent 生成对白                     │
│  │ dialogue    │  传入 target_word_count 约束                   │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ tts_trial   │  快速 TTS 估算 (可选: 采样3句取平均)            │
│  │             │  获取 actual_duration_ms                       │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ validate_   │  验证 actual_duration vs target_duration       │
│  │ duration    │  ±15% 容差内则通过                             │
│  └──────┬──────┘                                                │
│         │                                                        │
│    ┌────┴────┐                                                  │
│    │         │                                                  │
│    ▼         ▼                                                  │
│ ┌──────┐  ┌──────────┐                                          │
│ │commit│  │ prepare_ │  生成调整建议                             │
│ │_scene│  │ retry    │  (如: "需增加2句对白，约50字")             │
│ └──┬───┘  └────┬─────┘                                          │
│    │           │                                                │
│    │           └──────▶ generate_dialogue (重试)                │
│    │                                                            │
│    ▼                                                            │
│  ┌─────────────┐                                                │
│  │ rebalance_  │  (可选) 根据实际时长调整后续场景预算            │
│  │ budget      │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         └──────▶ select_next_scene (循环)                       │
│                                                                  │
│  ┌─────────────┐                                                │
│  │ assemble_   │  所有场景完成后:                                │
│  │ episode     │  - 生成完整 TTS + Timeline                     │
│  │             │  - 构建 Audio Timeline                         │
│  │             │  - 生成分镜帧                                  │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │ final_      │  验证总时长                                     │
│  │ validation  │  记录最终 ratio                                │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 关键算法

#### 2.4.1 预算分配算法

```python
def allocate_budget(
    total_duration_minutes: int,
    scenes: List[Dict[str, Any]],
    buffer_ratio: float = 0.05,
) -> List[SceneBudget]:
    """
    分配每个场景的时长预算。

    策略:
    1. 保留 5% buffer 用于场景间过渡
    2. 如果场景有 estimated_duration_seconds，按比例缩放
    3. 否则平均分配
    """
    total_seconds = total_duration_minutes * 60
    buffer_seconds = int(total_seconds * buffer_ratio)
    available_seconds = total_seconds - buffer_seconds

    # 检查是否有估算时长
    has_estimates = any(
        s.get("estimated_duration_seconds") for s in scenes
    )

    if has_estimates:
        # 按估算时长比例分配
        total_estimated = sum(
            s.get("estimated_duration_seconds", 30) for s in scenes
        )
        budgets = []
        for s in scenes:
            estimated = s.get("estimated_duration_seconds", 30)
            ratio = estimated / total_estimated
            target = int(available_seconds * ratio)
            budgets.append(SceneBudget(
                scene_number=s.get("scene_number", len(budgets) + 1),
                target_duration_seconds=target,
                target_word_count=int(target * 4.7),  # 约 280字/分钟（校准后）
                min_duration_seconds=int(target * 0.85),
                max_duration_seconds=int(target * 1.15),
            ))
    else:
        # 平均分配
        per_scene = available_seconds // len(scenes)
        budgets = [
            SceneBudget(
                scene_number=i + 1,
                target_duration_seconds=per_scene,
                target_word_count=int(per_scene * 4.7),
                min_duration_seconds=int(per_scene * 0.85),
                max_duration_seconds=int(per_scene * 1.15),
            )
            for i in range(len(scenes))
        ]

    return budgets
```

#### 2.4.2 字数验证与调整建议

```python
def compute_adjustment_hint(
    actual_word_count: int,
    actual_duration_ms: int,
    target_duration_seconds: int,
) -> tuple[str, str]:
    """
    计算调整建议。

    Returns:
        (rejection_reason, adjustment_hint)
    """
    target_ms = target_duration_seconds * 1000
    diff_ms = target_ms - actual_duration_ms
    diff_seconds = abs(diff_ms) / 1000

    # 估算需要增减的字数 (按 150字/分钟 = 2.5字/秒)
    words_per_second = 2.5
    word_diff = int(abs(diff_seconds) * words_per_second)

    if diff_ms > 0:
        # 时长不足
        reason = "duration_too_short"
        hint = (
            f"当前对白时长 {actual_duration_ms/1000:.1f}秒，"
            f"目标 {target_duration_seconds}秒，"
            f"差距 {diff_seconds:.1f}秒。"
            f"建议增加约 {word_diff} 字的对白（约 {word_diff // 20 + 1} 句）。"
            f"可以：1) 扩展现有对白的情感描写；2) 增加角色间的互动；3) 添加内心独白。"
        )
    else:
        # 时长过长
        reason = "duration_too_long"
        hint = (
            f"当前对白时长 {actual_duration_ms/1000:.1f}秒，"
            f"目标 {target_duration_seconds}秒，"
            f"超出 {diff_seconds:.1f}秒。"
            f"建议删减约 {word_diff} 字的对白（约 {word_diff // 20 + 1} 句）。"
            f"可以：1) 精简冗余对白；2) 合并相似内容；3) 删除非关键台词。"
        )

    return reason, hint
```

#### 2.4.3 TTS 快速估算 (采样模式)

```python
async def quick_tts_estimate(
    dialogues: List[Dict[str, Any]],
    sample_count: int = 3,
) -> int:
    """
    快速估算 TTS 总时长，避免完整生成。

    策略:
    1. 如果对白 <= 5 句，全量生成
    2. 否则采样 sample_count 句，计算平均速率
    3. 用速率 * 总字数估算总时长

    Returns:
        estimated_duration_ms
    """
    total_chars = sum(len(d.get("content", "")) for d in dialogues)

    if len(dialogues) <= 5:
        # 对白少，全量生成
        total_ms = 0
        for dlg in dialogues:
            duration_ms = await _tts_and_measure(dlg)
            total_ms += duration_ms
        return total_ms

    # 采样估算
    import random
    samples = random.sample(dialogues, min(sample_count, len(dialogues)))

    sample_chars = 0
    sample_ms = 0
    for dlg in samples:
        content = dlg.get("content", "")
        sample_chars += len(content)
        sample_ms += await _tts_and_measure(dlg)

    if sample_chars == 0:
        # 回退到默认速率
        ms_per_char = 150  # 默认每字 150ms
    else:
        ms_per_char = sample_ms / sample_chars

    return int(total_chars * ms_per_char)
```

### 2.5 Script Agent 改造

需要改造 `ScriptLangGraphAgent` 以支持字数约束：

```python
# 新增 prompt 变量
scene_generation_variables = {
    # ... 现有变量 ...
    "target_word_count": budget.target_word_count,
    "target_duration_seconds": budget.target_duration_seconds,
    "adjustment_hint": budget.adjustment_hint,  # 重试时提供
    "is_retry": budget.attempt_count > 1,
}

# 新增 prompt 模板片段
SCRIPT_WORD_COUNT_CONSTRAINT = """
## 时长约束
- **目标场景时长**: {{ target_duration_seconds }} 秒
- **目标对白字数**: 约 {{ target_word_count }} 个汉字
- 按照平均语速 280字/分钟 计算，对白总字数应接近目标

{% if is_retry and adjustment_hint %}
## 调整建议 (重试)
{{ adjustment_hint }}
{% endif %}

## 对白数量指导
- {{ target_duration_seconds }}秒 的场景通常需要 {{ (target_word_count / 25) | int }} - {{ (target_word_count / 20) | int }} 句对白
- 每句对白平均 20-30 个汉字
"""
```

## 3. 数据模型扩展

### 3.1 新增 Schema

```python
# app/schemas/duration_orchestrator.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SceneGenerationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMITTED = "committed"
    FAILED = "failed"

class SceneBudgetSchema(BaseModel):
    """场景时长预算"""
    scene_number: int
    target_duration_seconds: int
    target_word_count: int
    min_duration_seconds: int
    max_duration_seconds: int
    status: SceneGenerationStatus = SceneGenerationStatus.PENDING
    attempt_count: int = 0
    actual_duration_seconds: Optional[float] = None
    actual_word_count: Optional[int] = None
    last_rejection_reason: Optional[str] = None
    adjustment_hint: Optional[str] = None

class OrchestratorProgressSchema(BaseModel):
    """Orchestrator 进度"""
    episode_id: int
    total_scenes: int
    completed_scenes: int
    current_scene: Optional[int] = None
    current_attempt: int = 0
    committed_duration_seconds: float = 0.0
    target_duration_seconds: float
    phase: str  # allocating | generating | assembling | validating
    scene_budgets: List[SceneBudgetSchema] = []

class OrchestratorResultSchema(BaseModel):
    """Orchestrator 最终结果"""
    success: bool
    episode_id: int
    target_duration_seconds: float
    actual_duration_seconds: float
    duration_ratio: float
    scenes_generated: int
    scenes_retried: int
    total_attempts: int
    audio_timeline_url: Optional[str] = None
    storyboard_frames_count: int = 0
    reasoning: List[str] = []
```

### 3.2 Episode 扩展字段

```python
# 在 Episode.extra_metadata 中存储 orchestrator 状态

{
    "orchestrator": {
        "version": "1.0",
        "status": "completed",  # pending | in_progress | completed | failed
        "started_at": "2025-01-01T00:00:00Z",
        "completed_at": "2025-01-01T00:05:00Z",
        "scene_budgets": [...],
        "final_result": {
            "target_duration_seconds": 180,
            "actual_duration_seconds": 175.5,
            "duration_ratio": 0.975,
            "scenes_retried": 2,
            "total_attempts": 7,
        },
        "reasoning": [...]
    }
}
```

## 4. API 设计

### 4.1 新增 API 端点

```python
# POST /api/v1/episodes/{episode_id}/generate-with-duration-control
@router.post("/{episode_id}/generate-with-duration-control")
async def generate_episode_with_duration_control(
    episode_id: int,
    request: GenerateWithDurationControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateWithDurationControlResponse:
    """
    使用 Duration Orchestrator 生成剧集内容。

    1. 分配场景时长预算
    2. 逐场景生成对白 (带字数约束)
    3. TTS 快速估算验证
    4. 不达标则重试 (最多3次)
    5. 组装最终 Timeline 和分镜
    """
    pass

# GET /api/v1/episodes/{episode_id}/orchestrator-progress
@router.get("/{episode_id}/orchestrator-progress")
async def get_orchestrator_progress(
    episode_id: int,
    db: Session = Depends(get_db),
) -> OrchestratorProgressSchema:
    """获取 Orchestrator 当前进度"""
    pass

# POST /api/v1/episodes/{episode_id}/orchestrator-retry-scene
@router.post("/{episode_id}/orchestrator-retry-scene")
async def retry_scene_generation(
    episode_id: int,
    scene_number: int,
    db: Session = Depends(get_db),
) -> SceneBudgetSchema:
    """手动重试某个场景的生成"""
    pass
```

### 4.2 异步任务支持

```python
# 长时间运行，需要异步任务支持
async def generate_episode_with_duration_control_async(
    task_id: int,
    episode_id: int,
    params: dict,
) -> None:
    """
    异步执行 Duration Orchestrator。

    通过 task 表跟踪进度，支持中断恢复。
    """
    orchestrator = DurationOrchestratorAgent(...)

    # 支持从中断点恢复
    checkpoint = load_checkpoint(task_id)
    if checkpoint:
        orchestrator.restore_state(checkpoint)

    try:
        result = await orchestrator.run()
        save_result(task_id, result)
    except Exception as e:
        save_checkpoint(task_id, orchestrator.get_state())
        raise
```

## 5. 文件结构

```
ai-pic-backend/app/services/
├── duration_orchestrator/
│   ├── __init__.py
│   ├── agent.py                 # DurationOrchestratorAgent 主类
│   ├── state.py                 # OrchestratorState 定义
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── allocate_budget.py   # 预算分配节点
│   │   ├── generate_dialogue.py # 对白生成节点 (调用 Script Agent)
│   │   ├── tts_trial.py         # TTS 快速估算节点
│   │   ├── validate_duration.py # 时长验证节点
│   │   ├── commit_scene.py      # 场景提交节点
│   │   ├── prepare_retry.py     # 准备重试节点
│   │   ├── rebalance_budget.py  # 预算再平衡节点
│   │   ├── assemble_episode.py  # 剧集组装节点
│   │   └── final_validation.py  # 最终验证节点
│   ├── utils.py                 # 工具函数
│   └── constants.py             # 常量配置
│
├── script_agent.py              # 需改造: 支持字数约束
└── ...
```

## 6. 任务拆分

### Phase 1: 基础框架 (P0, 3天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 1.1 | 创建 `duration_orchestrator/` 目录结构 | 无 | 目录 + `__init__.py` |
| 1.2 | 实现 `OrchestratorState` 数据类 | 1.1 | `state.py` |
| 1.3 | 实现 `allocate_budget` 节点 | 1.2 | `nodes/allocate_budget.py` |
| 1.4 | 实现 `select_next_scene` 逻辑 | 1.2 | `agent.py` 部分 |
| 1.5 | 编写单元测试: 预算分配 | 1.3 | `tests/unit/test_budget_allocation.py` |

### Phase 2: 对白生成改造 (P0, 4天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 2.1 | 新增 `SCRIPT_WORD_COUNT_CONSTRAINT` prompt 模板 | 无 | `prompts/templates/script_word_count.txt` |
| 2.2 | 改造 `ScriptLangGraphAgent` 支持字数约束 | 2.1 | `script_agent.py` 修改 |
| 2.3 | 实现 `generate_dialogue` 节点 | 2.2, 1.4 | `nodes/generate_dialogue.py` |
| 2.4 | 实现 `compute_adjustment_hint` 函数 | 无 | `utils.py` |
| 2.5 | 编写单元测试: 对白生成 + 字数约束 | 2.3 | `tests/unit/test_dialogue_with_word_count.py` |

### Phase 3: TTS 估算与验证 (P1, 3天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 3.1 | 实现 `quick_tts_estimate` 采样估算 | 无 | `nodes/tts_trial.py` |
| 3.2 | 实现 `validate_duration` 节点 | 3.1 | `nodes/validate_duration.py` |
| 3.3 | 实现 `prepare_retry` 节点 (生成调整建议) | 2.4 | `nodes/prepare_retry.py` |
| 3.4 | 实现 `commit_scene` 节点 | 3.2 | `nodes/commit_scene.py` |
| 3.5 | 编写集成测试: TTS 估算准确性 | 3.1 | `tests/integration/test_tts_estimate.py` |

### Phase 4: 闭环控制 (P1, 3天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 4.1 | 实现 `rebalance_budget` 节点 (可选) | 3.4 | `nodes/rebalance_budget.py` |
| 4.2 | 组装 LangGraph StateGraph | 1.4, 2.3, 3.4 | `agent.py` 完整 |
| 4.3 | 实现条件边路由逻辑 | 4.2 | `agent.py` |
| 4.4 | 编写集成测试: 单场景闭环 | 4.3 | `tests/integration/test_scene_loop.py` |

### Phase 5: 剧集组装与最终验证 (P1, 3天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 5.1 | 实现 `assemble_episode` 节点 | 4.3 | `nodes/assemble_episode.py` |
| 5.2 | 实现 `final_validation` 节点 | 5.1 | `nodes/final_validation.py` |
| 5.3 | 集成到 `dialogue_audio_service.py` | 5.2 | 修改现有服务 |
| 5.4 | 编写端到端测试 | 5.3 | `tests/e2e/test_duration_orchestrator.py` |

### Phase 6: API 与异步任务 (P2, 2天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 6.1 | 新增 Pydantic schemas | 5.2 | `schemas/duration_orchestrator.py` |
| 6.2 | 实现 API 端点 | 6.1, 5.3 | `api/v1/endpoints/episodes/orchestrator.py` |
| 6.3 | 集成异步任务框架 | 6.2 | 修改 `async_tasks.py` |
| 6.4 | 编写 API 测试 | 6.3 | `tests/api/test_orchestrator_api.py` |

### Phase 7: 监控与可观测性 (P2, 1天)

| 任务 | 描述 | 依赖 | 产出 |
|------|------|------|------|
| 7.1 | 添加结构化日志 | 6.3 | 各节点日志增强 |
| 7.2 | 添加进度回调 (callbacks) | 7.1 | `agent.py` callbacks |
| 7.3 | 文档更新 | 7.2 | `docs/duration-orchestrator-guide.md` |

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| TTS 采样估算不准 | 时长偏差仍然存在 | 采样数量可配置；提供全量模式开关 |
| 重试次数过多 | 生成时间过长 | 设置最大重试次数；超时强制接受 |
| Script Agent 字数约束效果差 | 依赖 LLM 能力 | 多轮迭代优化 prompt；提供详细调整建议 |
| 预算再平衡复杂 | 后续场景受影响 | Phase 4 作为可选功能；先用简单平均 |

## 8. 验收标准

| 指标 | 目标值 |
|------|--------|
| 单场景时长偏差 | ≤ ±15% |
| 剧集总时长偏差 | ≤ ±10% |
| 平均重试次数 | ≤ 1.5 次/场景 |
| 端到端生成时间 | ≤ 现有流程 × 1.5 |
| 单元测试覆盖率 | ≥ 80% |

## 9. 附录

### 9.1 字数-时长换算参考

| 语速类型 | 字/分钟 | 字/秒 | 用途 |
|----------|---------|-------|------|
| 慢速 | 228 | 3.8 | 旁白、独白 |
| 正常 | 282 | 4.7 | 对话、叙述 |
| 快速 | 336 | 5.6 | 激动、紧张 |

### 9.2 容差设计依据

| 层级 | 容差 | 理由 |
|------|------|------|
| Episode (总时长) | ±10% | 用户对总时长敏感 |
| Scene (单场景) | ±15% | 允许场景间自然波动 |
| TTS 估算 vs 实际 | ±20% | 采样估算有固有误差 |
