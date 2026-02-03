---
id: 2026-02-03T14-00-00Z-cinematic-rules-validator
date: 2026-02-03T14:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, storyboard, cinematic]
related_paths:
  - ai-pic-backend/app/services/storyboard/validators/__init__.py
  - ai-pic-backend/app/services/storyboard/validators/cinematic_rules_validator.py
  - ai-pic-backend/app/services/storyboard/pipeline/storyboard_pipeline.py
  - ai-pic-backend/tests/unit/services/storyboard/validators/test_cinematic_rules_validator.py
  - tasks-agent-fix.md
summary: "创建影视语法规则校验器，检查180度规则、景别分布、光影连续性"
---

## User Prompt

继续 P0.4：影视语法规则校验

## Goals

1. 创建 `CinematicRulesValidator` 校验器
2. 实现 180 度规则检查（轴线跳跃检测）
3. 实现景别分布检查（避免全特写/全远景）
4. 实现光影连续性检查（日/夜突变检测）
5. 集成到 Storyboard 验证管线
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/storyboard/validators/cinematic_rules_validator.py`** (约 420 行)
   - `CinematicRulesValidator`: 核心校验器
     - `_classify_shot_type()`: 景别分类（特写/中景/全景等）
     - `_detect_camera_position()`: 相机位置检测（左/右/中）
     - `_detect_lighting()`: 光线条件检测（日/夜）
     - `_check_180_degree_rule()`: 180度规则检查
     - `_check_shot_variety()`: 景别多样性检查
     - `_check_lighting_continuity()`: 光影连续性检查
     - `_check_shot_rhythm()`: 镜头节奏检查（避免跳切）
   - 内置关键词库支持中英文识别

2. **`tests/unit/services/storyboard/validators/test_cinematic_rules_validator.py`** (约 280 行)
   - 26 个单元测试用例
   - 覆盖：景别分类、光线检测、位置翻转检测、多样性检查、光影连续性

### 修改文件

1. **`app/services/storyboard/validators/__init__.py`**
   - 导出 `CinematicRulesValidator`

2. **`app/services/storyboard/pipeline/storyboard_pipeline.py`**
   - 导入 `CinematicRulesValidator`
   - 添加到 `validators` 字典
   - 在 `validate_frames` 阶段调用

### 关键实现细节

- **180度规则检测**：追踪角色在画面中的位置（左/右），检测位置翻转
- **景别分类**：支持7种景别（大特写/特写/中近景/中景/中全景/全景/大全景）
- **光影检测**：识别日/夜关键词，检测同一场景内的突变
- **节奏检查**：检测连续3帧以上相同景别造成的跳切感

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/storyboard/validators/ -v
# 89 passed in 0.10s
```

## Next Steps

1. P0.4.7：E2E 分镜生成后运行规则校验
2. 剩余 P0 验证任务（1.7-1.8, 2.7, 3.7）
3. P1 中优先级任务

## Linked Commits

- feat(backend): add cinematic rules validator for storyboard validation
