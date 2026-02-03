---
id: 2026-02-03T12-00-00Z-info-gate-validator
date: 2026-02-03T12:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, info-gate]
related_paths:
  - ai-pic-backend/app/schemas/continuity.py
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/info_gate_validator.py
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/tests/unit/services/validators/test_info_gate_validator.py
  - tasks-agent-fix.md
summary: "创建信息门控校验器，防止对白引用未揭示的剧情信息"
---

## User Prompt

继续 P0.2：信息门控（剧情信息时序校验）

## Goals

1. 扩展 ContinuityLedger 增加 `revealed_info_timeline` 字段
2. 创建 `InfoGateValidator` 校验器
3. 实现对白扫描——检测是否引用未揭示的信息
4. 在 Script Agent 中集成信息门控校验
5. 生成修复建议
6. 补充单元测试

## Changes

### 修改文件

1. **`app/schemas/continuity.py`**
   - 新增 `RevealedInfoItem` 模型：记录信息揭示时间线
     - `info_key`: 信息唯一标识
     - `info_content`: 信息内容描述
     - `revealed_to`: 信息揭示给谁（角色名列表）
     - `revealed_at_episode`: 揭示的集数
     - `revealed_at_scene`: 揭示的场景号
     - `info_type`: 信息类型（identity/relationship/secret/event 等）
     - `is_public`: 是否为公开信息
   - 在 `ContinuityLedger` 中新增 `revealed_info_timeline` 字段

2. **`app/services/validators/__init__.py`**
   - 导出 `InfoGateValidator`, `InfoGateViolation`, `InfoGateContext` 等

3. **`app/services/script_agent.py`**
   - 导入 `InfoGateValidator`
   - 新增 `_validate_info_gate()` 方法
   - 在 `generate()` 中集成信息门控校验
   - 新增 `continuity_ledger` 参数

### 新增文件

1. **`app/services/validators/info_gate_validator.py`** (约 280 行)
   - `InfoGateSeverity`: 违规严重度枚举（ERROR/WARNING/INFO）
   - `InfoGateViolationType`: 违规类型枚举
     - `CHARACTER_KNOWS_TOO_MUCH`: 角色知道太多
     - `REFERENCES_FUTURE_EVENT`: 引用未来事件
     - `REFERENCES_UNREVEALED_SECRET`: 引用未揭示秘密
   - `InfoGateViolation`: 违规记录数据类
   - `InfoGateContext`: 校验上下文（角色知识、观众知识）
   - `InfoGateValidator`: 核心校验器
     - `register_revealed_info()`: 注册已揭示信息
     - `build_context()`: 构建指定时间点的知识上下文
     - `validate_dialogue()`: 校验单条对白
     - `validate_script_content()`: 校验整个剧本
     - `generate_fix_suggestions()`: 生成修复建议

2. **`tests/unit/services/validators/test_info_gate_validator.py`** (约 250 行)
   - 17 个单元测试用例
   - 覆盖：违规序列化、关键词提取、上下文构建、对白校验、整剧本校验、修复建议

### 关键实现细节

- **中文关键词提取**：使用 bi-gram 和 tri-gram 方式提取中文关键词，避免依赖分词库
- **知识上下文构建**：根据集数/场景号计算当前时间点每个角色和观众已知的信息
- **违规检测**：扫描对白中的关键词，匹配已注册的信息项，检查说话人是否应该知道该信息

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/ -v
# 45 passed in 0.07s
```

## Next Steps

1. P0.2.7：构造"角色说出未来剧情"的违规案例并验证阻断
2. P0.3：场景转场物理可行性校验

## Linked Commits

- feat(backend): add info gate validator for dialogue validation
