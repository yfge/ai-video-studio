---
id: 2026-02-03T23-00-00Z-ledger-compressor
date: 2026-02-03T23:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, continuity, compression, priority-sorting]
related_paths:
  - ai-pic-backend/app/services/continuity/ledger_compressor.py
  - ai-pic-backend/app/services/continuity/episode_continuity.py
  - ai-pic-backend/app/services/continuity/__init__.py
  - ai-pic-backend/tests/unit/services/continuity/__init__.py
  - ai-pic-backend/tests/unit/services/continuity/test_ledger_compressor.py
  - tasks-agent-fix.md
summary: "P1.6.5 优化连续性账本压缩，用优先级排序替代 FIFO 截断"
---

## User Prompt

继续 P1.6.5 连续性账本压缩优化（优先级排序替代 FIFO 截断）

## Goals

1. 创建优先级评分函数（facts, timeline, threads, info events）
2. 实现基于重要性的压缩策略
3. 替换原有 FIFO 截断逻辑
4. 补充单元测试

## Changes

### 新增文件

1. **`app/services/continuity/ledger_compressor.py`** (~230 行)
   - `CompressionConfig`: 压缩配置（max_facts=25, max_timeline=30, etc.）
   - `score_fact()`: 基于关键词/角色/长度评分
   - `score_timeline_item()`: 基于集数新近度/揭示数量/结局状态评分
   - `score_thread()`: 基于关键词/角色/问号评分
   - `score_info_event()`: 基于新近度/角色重要性/信息类型评分
   - `compress_ledger_by_priority()`: 主压缩函数

2. **`tests/unit/services/continuity/__init__.py`**
   - 测试模块初始化

3. **`tests/unit/services/continuity/test_ledger_compressor.py`** (~300 行)
   - 37 个单元测试用例
   - 覆盖: 事实评分、时间线评分、线索评分、信息事件评分、压缩配置、完整压缩流程

### 修改文件

1. **`app/services/continuity/episode_continuity.py`**
   - 导入 `compress_ledger_by_priority`
   - 将 `compact_continuity_ledger_for_prompt()` 改为调用新的优先级压缩函数

2. **`app/services/continuity/__init__.py`**
   - 导出新的压缩相关函数

### 关键实现细节

- **重要性关键词映射**:
  ```python
  IMPORTANCE_KEYWORDS_ZH = {
      "high": ["关键", "重要", "核心", "致命", "真相", "秘密", "身份", "死亡"],
      "medium": ["冲突", "转折", "悬念", "发现", "揭示", "隐藏", "证据", "线索"],
  }
  ```

- **评分维度**:
  - Facts: 关键词(+3/+1.5)、角色提及(+0.5/char)、长度(+0.5/+0.5)
  - Timeline: 新近度(up to +5)、揭示数(+1/each)、结局状态(+2)
  - Threads: 关键词评分、角色提及、问号(+1)
  - Info Events: 新近度(+3)、已知角色(+2)、观众知识(+1)

- **压缩后时间线重排**:
  - 按优先级筛选后，重新按集数排序保持时序

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/continuity/test_ledger_compressor.py -v
# 37 passed in 0.08s
```

## Next Steps

1. P0 剩余验证任务 (1.7-1.8, 2.7, 3.7, 4.7): E2E 验证
2. P2 任务：提示词模板重构、通用 Agent 框架等
3. 考虑将优先级评分逻辑与业务规则对齐（如主角权重更高）

## Linked Commits

- feat(backend): add priority-based continuity ledger compression
