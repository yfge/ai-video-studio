---
id: 2026-02-03T15-00-00Z-story-quality-validator
date: 2026-02-03T15:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, story, quality]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/story_quality_validator.py
  - ai-pic-backend/app/services/story_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_story_quality_validator.py
  - tasks-agent-fix.md
summary: "创建Story质量校验器，实现三幕结构/节奏分析/Hook评估/世界观一致性/内容限制检查"
---

## User Prompt

继续 P1.5 Story Agent Enhancement

## Goals

1. 创建 `StoryQualityValidator` 校验器
2. 实现三幕结构验证（设置/对抗/解决比例检查）
3. 实现节奏分析（开场/高潮/收尾节奏评分）
4. 实现 Hook/Cliffhanger 质量评估
5. 实现世界观一致性校验
6. 实现内容限制生成后校验
7. 集成到 Story Agent
8. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/story_quality_validator.py`** (~500 行)
   - `StoryQualityValidator`: 核心校验器
     - `_analyze_three_act_structure()`: 三幕结构分析
       - 理想比例: Act1 25%, Act2 50%, Act3 25%
       - 容差: ±10%
     - `_analyze_pacing()`: 节奏分析
       - 四阶段评分: opening/buildup/climax/resolution
       - 基于中文关键词密度计算
     - `_evaluate_hook_quality()`: Hook 质量评估
       - 检测开场和首集的吸引力关键词
       - 对比 hook_plan 进行评估
     - `_evaluate_cliffhanger_quality()`: Cliffhanger 评估
       - 检测各集结尾悬念关键词
     - `_check_worldbuilding_consistency()`: 世界观一致性
       - 检测时代与科技的矛盾（如古代+手机）
     - `_check_content_restrictions()`: 内容限制检查
       - 内置禁忌词列表
       - 支持自定义限制词
   - 辅助类:
     - `StoryQualityIssue`: 质量问题
     - `StoryQualityResult`: 校验结果
     - `ThreeActAnalysis`: 三幕分析结果
     - `PacingAnalysis`: 节奏分析结果

2. **`tests/unit/services/validators/test_story_quality_validator.py`** (~360 行)
   - 23 个单元测试用例
   - 覆盖: 三幕结构、节奏分析、Hook评估、Cliffhanger评估、世界观一致性、内容限制

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 StoryQualityValidator 相关类

2. **`app/services/story_agent.py`**
   - 导入 `StoryQualityValidator`
   - 在 `__init__` 初始化 `_quality_validator`
   - 添加 `_validate_story_quality()` 方法
   - 在 `generate()` 中集成质量校验（初次验证+修复循环）
   - 合并 `quality_validation` 结果到返回字典

### 关键实现细节

- **三幕结构检测**: 基于 `act_markers` 或 `episodes` 计算各幕比例
- **节奏关键词**: 中文关键词库 (紧张、冲突、高潮、解决等)
- **世界观检测**: 时代-科技不兼容规则表
- **禁忌内容**: 内置敏感词列表 (暴力、色情等)

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_story_quality_validator.py -v
# 23 passed in 0.08s

python -c "from app.services.story_agent import StoryLangGraphAgent; print('Import OK')"
# Import OK
```

## Next Steps

1. P1.6: Episode Agent 增强 (角色弧线、子情节平衡、伏笔追踪)
2. P1.7: Script Agent 增强 (对白真实性、展示别讲述)
3. 剩余 P0 验证任务 (1.7-1.8, 2.7, 3.7, 4.7)

## Linked Commits

- feat(backend): add story quality validator with three-act structure and pacing analysis
