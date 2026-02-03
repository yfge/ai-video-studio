---
id: 2026-02-03T17-00-00Z-script-quality-validator
date: 2026-02-03T17:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, script, quality]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/script_quality_validator.py
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_script_quality_validator.py
  - tasks-agent-fix.md
summary: "创建Script质量校验器，实现对白真实性/展示别讲述/潜台词/情绪弧线检查"
---

## User Prompt

继续 P1.7 Script Agent Enhancement

## Goals

1. 创建 `ScriptQualityValidator` 校验器
2. 实现对白真实性评分（自然度检测）
3. 实现"展示别讲述"检测（过多 exposition 警告）
4. 实现对白-动作比例检查（避免 talking heads）
5. 实现潜台词分析（角色说的 vs 想的）
6. 实现场景情绪弧线校验（入场情绪→出场情绪合理）
7. 集成到 Script Agent
8. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/script_quality_validator.py`** (~430 行)
   - `ScriptQualityValidator`: 核心校验器
     - `_score_dialogue_authenticity()`: 对白真实性评分
       - 检测自然对话模式（语气词、停顿、问句）
       - 惩罚过长句子和解说性关键词
     - `_calculate_exposition_ratio()`: 解说性对白比例
     - `_is_expository()`: 检测单条对白是否为解说
     - `_check_exposition()`: 批量检测过度解说
     - `_calculate_dialogue_action_ratio()`: 对白/动作比例
     - `_check_dialogue_action_ratio()`: 检测 "talking heads"
     - `_analyze_emotional_arcs()`: 场景情绪弧线分析
     - `_check_emotional_arcs()`: 情绪弧线问题检测
       - 检测平坦情绪（无变化）
       - 检测情绪跳跃过大
     - `_check_subtext()`: 潜台词检测
     - `_check_repetitive_dialogue()`: 重复对白检测
   - 辅助类:
     - `SceneEmotionalArc`: 场景情绪弧线数据
     - `ScriptQualityResult`: 校验结果

2. **`tests/unit/services/validators/test_script_quality_validator.py`** (~300 行)
   - 25 个单元测试用例
   - 覆盖: 真实性评分、解说检测、对白动作比例、情绪弧线、潜台词、重复检测

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 ScriptQualityValidator 相关类

2. **`app/services/script_agent.py`**
   - 导入 `ScriptQualityValidator`
   - 在 `__init__` 初始化 `_quality_validator`
   - 添加 `_validate_script_quality()` 方法
   - 在 `generate()` 中集成质量校验
   - 合并 `quality_validation` 结果到返回字典

### 关键实现细节

- **真实性评分**: 基于自然对话模式（语气词、问句、短句）和反模式（解说关键词、长句）
- **解说检测**: 关键词库 + 模式匹配 (正如你所知/让我解释/事实上等)
- **情绪分类**: 4 类情绪 (intense/positive/negative/neutral)，优先匹配 intense
- **潜台词检测**: 检测表面表达 + 内在张力的组合

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_script_quality_validator.py -v
# 25 passed in 0.07s

python -c "from app.services.script_agent import ScriptLangGraphAgent; print('Import OK')"
# Import OK
```

## Next Steps

1. P1.8: Timeline Agent 增强 (情绪曲线、多语言节奏)
2. P1.9: Duration Orchestrator 增强 (多 TTS Provider WPS 校准)
3. P1.10: Storyboard Agent 增强 (视觉连续性)
4. P1.11: Dialogue Audio Agent 重构

## Linked Commits

- feat(backend): add script quality validator with dialogue authenticity and show-don't-tell detection
