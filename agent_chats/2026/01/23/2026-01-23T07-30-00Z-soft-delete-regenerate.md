---
id: 2026-01-23T07-30-00Z-soft-delete-regenerate
date: 2026-01-23T07:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, soft_delete, regenerate, script]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - tasks.md
summary: "将 scripts regenerate 和 SceneBeat overwrite 改为 soft-delete 模式"
---

## User Prompt

继续推进 tasks.md 其余任务 - regenerate 创建新记录并软删旧记录

## Goals

1. 将 scripts regenerate 改为"新记录 + 旧记录软删"模式
2. 将 dialogue_audio_service 中 SceneBeat 的 hard delete 改为 soft delete

## Changes

### scripts_legacy.py - Script Regenerate

代码分析发现 `_process_script_regeneration_task` 函数（1476-1716 行）已经创建新 Script 记录，但未软删除旧 Script。

修改：在创建新 Script 后添加旧 Script 软删除：

```python
db.add(new_script)
db.commit()
db.refresh(new_script)

# 软删除旧剧本，保留历史记录但从列表隐藏
script.soft_delete(
    user_id=user_id,
    reason=f"regenerated_to_script_{new_script.id}",
)
db.commit()
```

### dialogue_audio_service.py - SceneBeat Overwrite

原代码使用 hard delete：
```python
if overwrite_beats:
    db.query(SceneBeat).filter(SceneBeat.scene_id == scene.id).delete(
        synchronize_session=False
    )
```

改为 soft delete：
```python
if overwrite_beats:
    existing_beats = (
        db.query(SceneBeat)
        .filter(
            SceneBeat.scene_id == scene.id,
            SceneBeat.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    for beat in existing_beats:
        beat.soft_delete(reason="dialogue_audio_overwrite")
```

## Validation

```bash
cd ai-pic-backend && python -m pytest tests/unit tests/test_story_structure_endpoints.py tests/test_story_structure_service.py -v --tb=short -q
# 结果：822 passed, 1 skipped
```

## Next Steps

1. **前端深链路** - 其余资源与深链路补齐 business_id 兜底，regenerate 后跳转到新记录
2. **E2E 验证** - Chrome 验证软删后列表/详情/再生成可用

## Linked Commits

- `691e9cb` feat(backend): change regenerate operations to soft-delete pattern
