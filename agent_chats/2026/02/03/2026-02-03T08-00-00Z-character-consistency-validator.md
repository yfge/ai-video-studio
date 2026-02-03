---
id: 2026-02-03T08-00-00Z-character-consistency-validator
date: 2026-02-03T08:00:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, agent-fix, refactor]
related_paths:
  - ai-pic-backend/app/services/validators/__init__.py
  - ai-pic-backend/app/services/validators/character_consistency_validator.py
  - ai-pic-backend/tests/unit/services/validators/__init__.py
  - ai-pic-backend/tests/unit/services/validators/test_character_consistency_validator.py
summary: "创建跨 Agent 角色一致性校验器，支持名称规范化、属性矛盾检测"
---

## User Prompt

开始执行 Agent 优化任务，从 P0.1.1 开始创建角色一致性校验器基础结构。

## Goals

1. 创建通用的角色一致性校验器，可在 Story/Episode/Script/Storyboard Agent 中复用
2. 实现角色名规范化（别名/昵称统一映射）
3. 实现角色属性一致性检查（性别/年龄/性格不矛盾）
4. 补充单元测试覆盖

## Changes

### 新增文件

1. **`app/services/validators/__init__.py`** (19 行)
   - 创建 validators 模块入口
   - 导出 `CharacterConsistencyValidator`, `CharacterProfile`, `CharacterValidationResult`

2. **`app/services/validators/character_consistency_validator.py`** (296 行)
   - `CharacterProfile` 数据类：存储角色规范化属性
   - `CharacterValidationResult` 数据类：标准化校验结果
   - `CharacterConsistencyValidator` 类：
     - `register_profiles()`: 注册角色卡
     - `resolve_name()`: 别名→标准名映射
     - `validate_names_in_text()`: 检测文本中的未知/错误角色名
     - `validate_character_attributes()`: 检测属性矛盾（性别/年龄/性格）

3. **`tests/unit/services/validators/test_character_consistency_validator.py`** (170 行)
   - 28 个单元测试用例
   - 覆盖：Profile 序列化、名称解析、别名映射、未知角色检测、属性矛盾检测

### 关键实现细节

- **性别判定**：使用关键词集合（male/female/男/女等）精确匹配，避免 "male" in "female" 的误判
- **年龄兼容性**：按年龄组（child/young/middle/elderly）分类，同组内兼容
- **性格冲突检测**：维护对立性格对（introverted/extroverted, kind/cruel 等）

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_character_consistency_validator.py -v
# 28 passed in 0.06s
```

## Next Steps

1. ~~P0.1.2：实现角色名规范化~~ ✅ 已完成
2. ~~P0.1.3：实现角色属性一致性检查~~ ✅ 已完成
3. ~~P0.1.4：在 Story Agent 中集成校验器~~ ✅ 已完成
4. P0.1.5：在 Episode Agent 中集成校验器
5. P0.1.6：在 Script Agent 中集成校验器

## Linked Commits

- feat(backend): add character consistency validator with tests
- feat(backend): integrate character validation into Story Agent
