---
id: 2026-02-03T20-00-00Z-duration-quality-validator
date: 2026-02-03T20:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, duration, tts]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/duration_quality_validator.py
  - ai-pic-backend/tests/unit/services/validators/test_duration_quality_validator.py
  - tasks-agent-fix.md
summary: "创建Duration质量校验器，实现多TTS Provider WPS校准/跨剧集时长平衡/词数分布/重试收敛分析"
---

## User Prompt

继续 P1.9 Duration Orchestrator Enhancement

## Goals

1. 创建 `DurationQualityValidator` 校验器
2. 实现多 TTS Provider WPS 校准（VolcEngine/Google/MiniMax 各自常数）
3. 实现跨剧集时长平衡检测（Ep1~EpN 时长分布均匀）
4. 实现场景内词数分布均衡（避免头重脚轻）
5. 实现重试收敛分析（检测病态场景）
6. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/duration_quality_validator.py`** (~500 行)
   - `DurationQualityValidator`: 核心校验器
     - `get_calibrated_wps()`: 获取 Provider/语言/语速组合的 WPS
     - `estimate_duration_with_provider()`: 基于 Provider 的时长估算
     - `analyze_word_distribution()`: 场景词数分布分析
     - `check_word_distribution()`: 分布问题检测（前重/后重）
     - `analyze_retry_convergence()`: 重试收敛模式分析
     - `check_retry_convergence()`: 病态场景/振荡检测
     - `analyze_episode_balance()`: 跨剧集时长平衡分析
     - `validate()`: 综合校验入口
   - 辅助类:
     - `DurationQualityIssue`: 问题描述
     - `DurationQualityIssueType`: 问题类型枚举
     - `DurationQualitySeverity`: 严重程度枚举
     - `RetryAnalysis`: 重试分析结果
     - `WordDistributionAnalysis`: 词数分布分析结果
     - `DurationQualityResult`: 校验结果

2. **`tests/unit/services/validators/test_duration_quality_validator.py`** (~350 行)
   - 35 个单元测试用例
   - 覆盖: WPS校准、时长估算、词数分布、重试收敛、剧集平衡、综合校验

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 DurationQualityValidator 相关类

### 关键实现细节

- **多 TTS Provider WPS 配置**:
  ```python
  WPS_BY_PROVIDER = {
      "volcengine": {
          "zh": {"slow": 3.5, "normal": 4.5, "fast": 5.5},
          "en": {"slow": 2.3, "normal": 3.0, "fast": 3.8},
          ...
      },
      "google": {
          "zh": {"slow": 3.6, "normal": 4.6, "fast": 5.6},
          ...
      },
      "minimax": {
          "zh": {"slow": 4.0, "normal": 5.0, "fast": 6.0},
          ...
      },
      "default": {
          "zh": {"slow": 3.8, "normal": 4.7, "fast": 5.6},
          ...
      }
  }
  ```

- **词数分布阈值**:
  - 前重阈值: >65% 在前半部分
  - 后重阈值: <35% 在前半部分
  - Z-score 异常检测: > 2.0

- **重试收敛检测**:
  - 振荡阈值: >3 次方向变化
  - 收敛率阈值: <10% 改善 = 未收敛
  - 病态场景: 达到重试上限但未收敛

- **剧集平衡检测**:
  - 变异系数阈值: CV > 15% 视为不平衡
  - Z-score 异常检测: > 2.0 的剧集为异常值

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_duration_quality_validator.py -v
# 35 passed in 0.06s
```

## Next Steps

1. P1.10: Storyboard Agent 增强 (视觉连续性)
2. P1.11: Dialogue Audio Agent 重构
3. 集成 DurationQualityValidator 到 Duration Orchestrator 流程
4. 完成 P0 剩余验证任务 (1.7-1.8, 2.7, 3.7, 4.7)

## Linked Commits

- feat(backend): add duration quality validator with multi-TTS provider WPS calibration
