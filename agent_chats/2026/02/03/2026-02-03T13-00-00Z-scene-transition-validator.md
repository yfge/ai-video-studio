---
id: 2026-02-03T13-00-00Z-scene-transition-validator
date: 2026-02-03T13:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, scene-transition]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/scene_transition_validator.py
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_scene_transition_validator.py
  - tasks-agent-fix.md
summary: "创建场景转场物理可行性校验器，检查地理/时间/角色状态连续性"
---

## User Prompt

继续 P0.3：场景转场物理可行性校验

## Goals

1. 创建 `SceneTransitionValidator` 校验器
2. 实现地理连续性检查（跨城市需合理旅行时间）
3. 实现时间连续性检查（时间段转换需合理）
4. 实现角色状态连续性检查（受伤状态与动作冲突）
5. 在 Script Agent 中集成转场校验
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/scene_transition_validator.py`** (约 350 行)
   - `TransitionSeverity`: 问题严重度枚举（ERROR/WARNING/INFO）
   - `TransitionIssueType`: 问题类型枚举
     - `GEOGRAPHIC_IMPOSSIBILITY`: 地理不可能
     - `TIME_DISCONTINUITY`: 时间不连贯
     - `CHARACTER_STATE_VIOLATION`: 角色状态冲突
   - `TransitionIssue`: 转场问题数据类
   - `SceneInfo`: 场景信息提取数据类
   - `SceneTransitionValidator`: 核心校验器
     - `_normalize_time()`: 时间标准化（早上/中午/夜晚等）
     - `_extract_city()`: 从地点提取城市
     - `_check_time_transition()`: 时间转场检查
     - `_check_geographic_transition()`: 地理转场检查
     - `_detect_character_state()`: 角色状态检测（受伤/昏迷等）
     - `_check_character_state_transition()`: 角色状态连续性检查
     - `extract_scene_info()`: 从场景提取校验信息
     - `validate_transitions()`: 校验所有场景转场
     - `generate_fix_suggestions()`: 生成修复建议

2. **`tests/unit/services/validators/test_scene_transition_validator.py`** (约 270 行)
   - 24 个单元测试用例
   - 覆盖：时间规范化、城市提取、时间转场、地理转场、角色状态检测、完整校验流程

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 `SceneTransitionValidator`, `TransitionIssue`, `SceneInfo` 等

2. **`app/services/script_agent.py`**
   - 导入 `SceneTransitionValidator`
   - 新增 `_validate_scene_transitions()` 方法
   - 在 `generate()` 中集成转场校验

### 关键实现细节

- **城市旅行时间表**：内置主要城市间的旅行时间（北京-上海约5小时）
- **时间转场规则**：定义合法的时间段转换（早上→中午→下午→傍晚→夜晚→黎明）
- **角色状态冲突**：定义限制性状态（受伤/昏迷）与冲突动作（跑步/打斗）
- **严重度分级**：ERROR 表示物理不可能，WARNING 表示需要注意

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/ -v
# 69 passed in 0.08s
```

## Next Steps

1. P0.3.7：构造不合理转场案例并验证检测
2. P0.4：影视语法规则校验（180度规则、景别分布等）

## Linked Commits

- feat(backend): add scene transition validator for script validation
