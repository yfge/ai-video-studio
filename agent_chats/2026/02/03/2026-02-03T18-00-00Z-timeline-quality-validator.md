---
id: 2026-02-03T18-00-00Z-timeline-quality-validator
date: 2026-02-03T18:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, timeline, rhythm]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/timeline_quality_validator.py
  - ai-pic-backend/tests/unit/services/validators/test_timeline_quality_validator.py
  - tasks-agent-fix.md
summary: "创建Timeline质量校验器，实现情绪曲线/多语言节奏/戏剧停顿/音节时序估算"
---

## User Prompt

继续 P1.8 Timeline Agent Enhancement

## Goals

1. 创建 `TimelineQualityValidator` 校验器
2. 实现情绪曲线分析（紧张/舒缓波动可视化）
3. 实现多语言节奏适配（中文/英文/日文/韩文不同 WPS）
4. 实现戏剧停顿检测（笑点/泪点留白）
5. 实现 TTS 音节级时序分析（替代词数估算）
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/timeline_quality_validator.py`** (~500 行)
   - `TimelineQualityValidator`: 核心校验器
     - `_detect_language()`: 多语言检测（中/英/日/韩）
     - `_calculate_average_wps()`: 计算平均语速
     - `_check_rhythm()`: 节奏检查（过快/过慢）
     - `_analyze_emotion_curve()`: 情绪曲线分析
       - 计算平均强度和方差
       - 检测波峰和波谷
       - 判断是否有情绪弧线
     - `_check_emotion_curve()`: 情绪曲线问题检测
       - 平坦曲线检测
       - 过于波动检测
     - `_calculate_pause_ratio()`: 停顿比例计算
     - `_check_dramatic_pauses()`: 戏剧停顿检测
       - 笑点/泪点/悬念/动作后停顿
       - 过长停顿检测
     - `_check_duration_drift()`: 时长漂移检测
     - `estimate_duration_syllable_level()`: 音节级时长估算
       - 中文：字符 + 标点停顿
       - 日语：假名 + 汉字音节
       - 英语：音节计数
       - 韩语：音节块计数
   - 辅助类:
     - `EmotionPoint`: 情绪数据点
     - `EmotionCurveAnalysis`: 情绪曲线分析结果
     - `TimelineQualityResult`: 校验结果

2. **`tests/unit/services/validators/test_timeline_quality_validator.py`** (~320 行)
   - 28 个单元测试用例
   - 覆盖: 语言检测、WPS计算、节奏检查、情绪曲线、戏剧停顿、时长估算

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 TimelineQualityValidator 相关类

### 关键实现细节

- **多语言 WPS 配置**:
  - 中文: slow=3.8, normal=4.7, fast=5.6 字/秒
  - 英文: slow=2.5, normal=3.2, fast=4.0 词/秒
  - 日语: slow=4.0, normal=5.0, fast=6.0 音节/秒
  - 韩语: slow=3.5, normal=4.5, fast=5.5 音节/秒

- **情绪强度关键词**: 分为高/中/低三档
- **戏剧停顿触发**: comedy/drama/suspense/action 四类
- **停顿阈值**: 最小 500ms, 最大 3000ms

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_timeline_quality_validator.py -v
# 28 passed in 0.08s
```

## Next Steps

1. P1.9: Duration Orchestrator 增强 (多 TTS Provider WPS 校准)
2. P1.10: Storyboard Agent 增强 (视觉连续性)
3. P1.11: Dialogue Audio Agent 重构
4. 集成 TimelineQualityValidator 到具体 Agent 流程

## Linked Commits

- feat(backend): add timeline quality validator with emotion curve and multi-language rhythm analysis
