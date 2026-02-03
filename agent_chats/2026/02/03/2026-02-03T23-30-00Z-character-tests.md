---
id: 2026-02-03T23-30-00Z-character-tests
date: 2026-02-03T23:30:00Z
participants: [human, claude]
models: [claude-opus-4-5]
tags: [backend, validator, testing, character-consistency]
related_paths:
  - ai-pic-backend/app/services/validators/character_consistency_validator.py
  - ai-pic-backend/tests/unit/services/validators/test_character_consistency_validator.py
  - tasks-agent-fix.md
summary: "P0 1.7 补充角色一致性校验单元测试（正例+违例），修复性别检测bug"
---

## User Prompt

继续 P0 1.7 补充角色一致性校验单元测试

## Goals

1. 添加违例场景测试（多重矛盾、中文性别、性格冲突等）
2. 添加边界条件测试（空文本、null值、特殊字符等）
3. 添加正例场景测试（一致性通过的各种情况）
4. 修复发现的性别检测bug

## Changes

### 修改文件

1. **`app/services/validators/character_consistency_validator.py`**
   - 修复 `_attributes_compatible()` 中的性别检测bug
   - 问题："female" 包含 "male" 子串，导致误判
   - 解决方案：使用 regex word boundary (`\b`) 进行精确匹配

2. **`tests/unit/services/validators/test_character_consistency_validator.py`**
   - 添加 `TestViolationScenarios` 类 (9个测试)
     - 多重属性矛盾检测
     - 中文性别矛盾
     - 儿童→老年年龄矛盾
     - 性格对立检测
     - 舞台指示角色提取
     - 混合语言对话
     - 未知角色检测
   - 添加 `TestEdgeCases` 类 (8个测试)
     - 空文本处理
     - 无对话格式文本
     - 纯空白文本
     - null属性值
     - 空性格列表
     - 仅名称的profile
     - 超长角色名
     - 特殊字符角色名
   - 添加 `TestPassingScenarios` 类 (6个测试)
     - 全部已知角色通过
     - 一致性别通过（中英跨语言）
     - 同年龄组通过
     - 非冲突性格通过
     - 部分属性验证通过
     - 旁白不被标记

### 关键修复

性别检测bug修复：

```python
# 修复前（有bug）
e_male = any(g in e for g in gender_male)  # "male" in "female" = True!

# 修复后（使用word boundary）
def is_gender(text: str, keywords: set) -> bool:
    if text in keywords:
        return True
    for kw in keywords:
        if kw.isascii():
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text):
                return True
        else:
            if kw in text:  # Chinese substring OK
                return True
    return False
```

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/validators/test_character_consistency_validator.py -v
# 51 passed in 0.07s
```

测试覆盖：
- 原有测试：28个
- 新增测试：23个（违例9 + 边界8 + 正例6）
- 总计：51个

## Next Steps

1. P0 1.8: E2E 跑通角色一致性校验链路
2. P0 2.7: 构造信息门控违规案例验证
3. P0 3.7: 构造不合理转场案例验证
4. P0 4.7: E2E 分镜生成后运行规则校验

## Linked Commits

- test(backend): add comprehensive character consistency validator tests
