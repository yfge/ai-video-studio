---
id: 2025-12-26T12-20-00Z-script-regeneration-versioning
date: 2025-12-26T12:20:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, script, versioning]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
summary: "Script regeneration now creates new version instead of overwriting"
---

## User Prompt

User asked: "现在剧本重新生成时是直接把原有的给覆盖了么？"

Translation: "Is script regeneration currently overwriting the original?"

After confirming yes, user selected: "1. 创建新剧本 - 保留原剧本，新建一个版本"

Translation: "Create new script - keep original, create new version"

## Goals

1. Preserve original scripts when regenerating
2. Create new script version with version number increment
3. Track parent-child relationship in metadata

## Changes

### scripts_legacy.py - `_process_script_regeneration_task`

**Before**: Direct update of existing script record
```python
script.content = script_content
script.scenes = scenes
# ... direct updates
db.commit()
```

**After**: Create new Script record
- Version increment: `1.0` → `1.1`, `1.1` → `1.2`, etc.
- Parent tracking in `extra_metadata`:
  - `parent_script_id`: Original script's database ID
  - `parent_script_business_id`: Original script's business ID
  - `regenerated_from_version`: Previous version string
- Title with version suffix: `"剧本 - 第1集 (v1.1)"`
- New Script record created via `db.add(new_script)`
- Task result points to new script: `script:{new_script.id}`

## Validation

1. Import check: `from app.api.v1.endpoints.scripts_legacy import _process_script_regeneration_task` - OK
2. Script agent tests: 7/7 passed

## Next Steps

1. End-to-end test script regeneration in browser
2. Verify new script appears in episode's script list
3. Confirm original script preserved

## Linked Commits

- 4f8af8a feat(script): create new version on regeneration instead of overwriting
