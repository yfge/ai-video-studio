---
id: 2026-02-03T21-00-00Z-visual-continuity-validator
date: 2026-02-03T21:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, storyboard, visual]
related_paths:
  - ai-pic-backend/app/services/storyboard/validators/__init__.py
  - ai-pic-backend/app/services/storyboard/validators/visual_continuity_validator.py
  - ai-pic-backend/tests/unit/services/storyboard/validators/test_visual_continuity_validator.py
  - tasks-agent-fix.md
summary: "创建视觉连续性校验器，实现服装/道具/发型跨帧一致性/动作物理可行性/构图规则/对白视觉同步"
---

## User Prompt

继续 P1.10 Storyboard Agent Enhancement

## Goals

1. 创建 `VisualContinuityValidator` 校验器
2. 实现视觉连续性检测（服装/道具/发型跨帧一致）
3. 实现动作物理可行性校验（人物不能"瞬移"）
4. 实现构图规则提示（三分法/引导线/景深）
5. 实现对白-视觉同步校验（说话时嘴要动）
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/storyboard/validators/visual_continuity_validator.py`** (~500 行)
   - `VisualContinuityValidator`: 核心校验器
     - `_check_costume_continuity()`: 服装连续性检测
     - `_check_hairstyle_continuity()`: 发型连续性检测
     - `_check_prop_continuity()`: 道具连续性检测
     - `_check_movement_feasibility()`: 移动物理可行性检测
     - `_check_pose_transitions()`: 姿态转换合理性检测
     - `_check_composition_suggestions()`: 构图规则建议
     - `_check_dialogue_visual_sync()`: 对白-视觉同步检测
   - 辅助方法:
     - `_extract_visual_elements()`: 从描述中提取视觉元素
     - `_extract_position()`: 提取位置信息
     - `_extract_pose()`: 提取姿态信息
     - `_find_inconsistencies()`: 查找不一致元素
     - `_find_disappearing_elements()`: 检测消失的道具
     - `_is_teleportation()`: 检测瞬移
     - `_elements_similar()`: 元素相似度判断

2. **`tests/unit/services/storyboard/validators/test_visual_continuity_validator.py`** (~400 行)
   - 27 个单元测试用例
   - 覆盖: 服装/发型/道具连续性、移动/姿态可行性、构图建议、对白同步

### 修改文件

1. **`app/services/storyboard/validators/__init__.py`**
   - 导出 VisualContinuityValidator

### 关键实现细节

- **视觉元素关键词**:
  - 服装: 穿着/衣服/裙子/西装/T恤/衬衫...
  - 发型: 长发/短发/卷发/直发/马尾...
  - 道具: 手持/拿着/戴着/眼镜/帽子/包...

- **位置关键词**: 左侧/右侧/中央/前景/背景...

- **姿态关键词**: 坐着/站着/躺着/走动/奔跑...

- **无效姿态转换**:
  - 躺着 → 奔跑 (需要中间过渡)
  - 奔跑 → 躺着
  - 坐着 → 奔跑

- **构图规则检测**:
  - 三分法 (rule of thirds)
  - 引导线 (leading lines)
  - 景深 (depth of field)

- **对白同步检测**:
  - 检测对白帧是否有说话视觉提示
  - 关键词: 说话/开口/张嘴/speaking/mouth open...

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/storyboard/validators/test_visual_continuity_validator.py -v
# 27 passed in 0.06s
```

## Next Steps

1. P1.11: Dialogue Audio Agent 重构
2. P1.6.5: 连续性账本压缩优化
3. 完成 P0 剩余验证任务 (1.7-1.8, 2.7, 3.7, 4.7)
4. 集成 VisualContinuityValidator 到 Storyboard Pipeline

## Linked Commits

- feat(backend): add visual continuity validator for storyboard frames
