---
id: 2026-02-03T16-00-00Z-episode-quality-validator
date: 2026-02-03T16:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, episode, quality]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/episode_quality_validator.py
  - ai-pic-backend/app/services/episode_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_episode_quality_validator.py
  - tasks-agent-fix.md
summary: "创建Episode质量校验器，实现角色弧线/子情节平衡/戏剧张力/伏笔追踪"
---

## User Prompt

继续 P1.6 Episode Agent Enhancement

## Goals

1. 创建 `EpisodeQualityValidator` 校验器
2. 实现角色弧线追踪（目标/关系/状态跨集演变）
3. 实现子情节平衡检查（主线/支线屏幕时间比例）
4. 实现戏剧张力递增检测（stakes 跨集升级）
5. 实现伏笔/回收追踪（setup in Ep N, payoff in Ep N+M）
6. 集成到 Episode Agent
7. 补充单元测试

## Changes

### 新增文件

1. **`app/services/validators/episode_quality_validator.py`** (~450 行)
   - `EpisodeQualityValidator`: 核心校验器
     - `_track_character_arcs()`: 角色弧线追踪
       - 从 episode characters 和 continuity 提取目标/状态
       - 跟踪关系变化
     - `_check_arc_progression()`: 弧线停滞检测
       - 检测多集中目标/状态无变化的角色
     - `_analyze_subplot_balance()`: 子情节平衡分析
       - 关键词库: main/romance/conflict/mystery/growth
       - 计算各支线比例
     - `_analyze_tension_progression()`: 张力递增分析
       - 中文张力关键词库 (危机/对决/冲突等)
       - 逐集张力评分
     - `_check_tension_progression()`: 张力模式检测
       - 检测平台期 (3+ 集相似分数)
       - 检测中段张力骤降
       - 检测整体下降趋势
     - `_track_foreshadowing()`: 伏笔追踪
       - 从 continuity_ledger 提取 open/resolved threads
       - 从内容扫描 setup/payoff 关键词
     - `_check_foreshadowing()`: 伏笔问题检测
       - 未回收伏笔过多 (unfired Chekhov)
       - 回收过快 (premature payoff)
   - 辅助类:
     - `CharacterArc`: 角色弧线数据
     - `ForeshadowingItem`: 伏笔/回收记录
     - `EpisodeQualityResult`: 校验结果

2. **`tests/unit/services/validators/test_episode_quality_validator.py`** (~250 行)
   - 25 个单元测试用例
   - 覆盖: 弧线追踪、弧线停滞、子情节平衡、张力计算、张力模式、伏笔追踪

### 修改文件

1. **`app/services/validators/__init__.py`**
   - 导出 EpisodeQualityValidator 相关类

2. **`app/services/episode_agent.py`**
   - 导入 `EpisodeQualityValidator`
   - 在 `__init__` 初始化 `_quality_validator`
   - 添加 `_validate_episode_quality()` 方法
   - 在 `generate()` 中集成质量校验
   - 合并 `quality_validation` 结果到返回字典

### 关键实现细节

- **角色弧线**: 从 characters 和 continuity.characters 两个来源提取
- **子情节检测**: 基于关键词密度计算各支线比例
- **张力评分**: 0-1 范围，基于关键词密度和内容长度归一化
- **伏笔追踪**: 结合 continuity_ledger 和内容扫描

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_episode_quality_validator.py -v
# 25 passed in 0.08s

python -c "from app.services.episode_agent import EpisodeLangGraphAgent; print('Import OK')"
# Import OK
```

## Next Steps

1. P1.6.5: 优化连续性账本压缩（优先级排序替代 FIFO 截断）
2. P1.7: Script Agent 增强 (对白真实性、展示别讲述)
3. P1.8-11: 其余中优先级任务

## Linked Commits

- feat(backend): add episode quality validator with arc tracking and tension analysis
