---
id: 2025-12-24T08-30-00Z-timeline-agent-implementation
date: 2025-12-24T08:30:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, langgraph, audio, timeline, react, frontend]
related_paths:
  - ai-pic-backend/app/services/timeline_agent/__init__.py
  - ai-pic-backend/app/services/timeline_agent/schemas.py
  - ai-pic-backend/app/services/timeline_agent/agent.py
  - ai-pic-backend/app/services/timeline_agent/constants.py
  - ai-pic-backend/app/services/timeline_agent/utils.py
  - ai-pic-backend/app/services/audio/dialogue_processor.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/prompts/templates.py
  - ai-pic-backend/app/prompts/templates/timeline_gap_reasoning.txt
  - ai-pic-backend/app/prompts/templates/timeline_gap_repair.txt
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/tests/unit/services/timeline_agent/test_timeline_agent.py
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/components/features/episode/AudioTimelineSection.tsx
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/utils/api/endpoints/script.endpoints.ts
summary: "Implemented intelligent timeline agent using LangGraph ReAct pattern with model selection UI"
---

## User Prompt

用户指出当前对白生成使用固定的 300ms 间隔，没有与剧本的分镜及场景描述关联。要求：
1. 利用 LangGraph Agent 能力
2. 使用 ReAct 机制进行时间预估和判断
3. 形成真正的分镜时间轴
4. 保证生产级可用

**追加需求**: 生成对白音轨时需要可以选择模型，使用通用的模型列表。

## Goals

1. 实现基于 LangGraph 的智能时间轴生成代理
2. 使用 ReAct 模式（Reason + Act + Observe + Reflect）
3. 根据情绪、场景节奏、分镜描述动态计算停顿时长
4. 提供 3 层降级回退机制保证生产稳定性
5. 集成到现有 dialogue_audio_service 管道
6. 添加模型选择功能，允许用户选择用于时间轴计算的 LLM 模型

## Changes

### 新增文件

1. **timeline_agent/ 模块**
   - `__init__.py` - 模块导出
   - `schemas.py` (~150行) - Pydantic 数据模型
     - SceneContext, DialogueContext, TimingDecision, TimingPlan
     - TimelineAgentState 用于 LangGraph 状态管理
   - `agent.py` (~250行) - LangGraph Agent 主体
     - 6个节点: analyze_scene → think_timing → propose_gaps → validate_rhythm → adjust_timing → finalize
     - ReAct 循环: 最多 2 次修复尝试
   - `constants.py` (~100行) - 情绪权重、约束常量、系统提示词
   - `utils.py` (~150行) - 辅助函数
     - 情绪提取、冲突推断、节奏计算
     - 规则引擎回退计算

2. **提示词模板**
   - `timeline_gap_reasoning.txt/yaml` - 推理提示词
   - `timeline_gap_repair.txt/yaml` - 修复提示词

3. **单元测试**
   - `tests/unit/services/timeline_agent/test_timeline_agent.py` (23 tests)

### 修改文件

1. **dialogue_processor.py**
   - 新增 `plan_scene_segments_intelligent()` 异步函数
   - 新增 `_build_segments_with_timing()` 辅助函数
   - 支持 timing_map 动态间隔

2. **dialogue_audio_service.py**
   - 新增导入 `plan_scene_segments_intelligent`
   - `generate_scene_dialogue_audio()` 添加 `use_intelligent_timing` 参数
   - 构建 scene_context 传递给 Agent

3. **templates.py**
   - 新增 `TIMELINE_GAP_REASONING`, `TIMELINE_GAP_REPAIR` 枚举
   - 更新 TEMPLATE_CATEGORIES 映射

4. **scripts_legacy.py**
   - `ScriptDialogueAudioGenerateRequest` 新增 `timing_model` 参数
   - `_process_script_dialogue_audio_task` 传递 `timing_model` 给服务

### 前端修改

1. **AudioTimelineSection.tsx**
   - 添加 `timingModel` 和 `setTimingModel` props
   - 集成 `useAvailableModels` hook 获取模型列表
   - 新增模型选择下拉框 UI

2. **page.tsx (episodes/[id])**
   - 解构 `timingModel` 和 `setTimingModel` 状态
   - 传递给 `AudioTimelineSection` 组件
   - `handleGenerateSceneDialogueAudio` 携带 `timing_model` 参数

3. **useEpisodeDetail.ts**
   - 新增 `timingModel` 状态管理
   - 返回 `timingModel` 和 `setTimingModel`

4. **script.endpoints.ts & api.ts**
   - `generateSceneDialogueAudioAsync` payload 新增 `timing_model` 字段

### 架构设计

```
ReAct 状态机:
analyze_scene ──► think_timing ──► propose_gaps ──► validate_rhythm
                                                         │
                                              ┌──────────┴──────────┐
                                              │                     │
                                         [passed]              [failed]
                                              │                     │
                                         finalize ◄── adjust_timing ◄┘
                                              │         (max 2次)
                                          [END]

回退策略:
Level 1: LangGraph Agent + LLM 推理
    ↓ 失败
Level 2: 规则引擎 + 情绪权重
    ↓ 失败
Level 3: 固定间隔 (300ms)
```

### 关键约束

```python
MIN_GAP_MS = 100       # 最短间隔
MAX_GAP_MS = 5000      # 最长间隔
MIN_AVG_GAP_MS = 200   # 平均最短
MAX_AVG_GAP_MS = 1500  # 平均最长
```

### 情绪过渡权重示例

```python
("angry", "calm"): 1.8,   # 愤怒→平静 需要更长停顿
("calm", "calm"): 0.9,    # 相同情绪 稍短停顿
("angry", "angry"): 0.8,  # 快速愤怒交换
```

## Validation

1. **导入检查**: `python -c "from app.services.timeline_agent import ..."` 通过
2. **单元测试**: 23 tests passed
   - SceneContextBuilding: 8 tests
   - DialogueContextBuilding: 2 tests
   - EmotionTransitionWeights: 4 tests
   - FallbackTiming: 2 tests
   - RhythmScore: 3 tests
   - TimingPlanValidation: 2 tests
   - SceneContext: 2 tests
3. **前端 lint**: `npm run lint` 通过

## Next Steps

1. **E2E 测试**: 使用真实场景数据验证 LLM 推理效果
2. **缓存实现**: 将 timing 决策持久化到 Scene.extra_metadata
3. **性能优化**: 考虑批量处理多个场景
4. **监控**: 添加指标追踪 LLM 调用成功率、回退率
5. ~~**前端集成**: 暴露 API 开关控制 `use_intelligent_timing`~~ ✅ 已完成

## Linked Commits

- `1e04e5e` feat(timeline): add intelligent timing agent with model selection
