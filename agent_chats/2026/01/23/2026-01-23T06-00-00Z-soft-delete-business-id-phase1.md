---
id: 2026-01-23T06-00-00Z-soft-delete-business-id-phase1
date: 2026-01-23T06:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, soft_delete, business_id, story_structure]
related_paths:
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/scenes.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/shots.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/beats.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure/environments.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - tasks.md
summary: "补齐 story_structure 软删除过滤、将硬删除改为软删除、新增 scenes/shots/beats 的 business_id CRUD 端点"
---

## User Prompt

继续推进 tasks.md 其余任务 - 选择「全局软删除 + business_id」

## Goals

1. 补齐 story_structure_service 中缺少的 `is_deleted=false` 过滤
2. 将 scenes/shots/scene_beats/environments 的硬删除改为软删除
3. 新增 scenes/shots/scene_beats 的 business_id CRUD 端点

## Changes

### 补齐软删除过滤 (story_structure_service.py)

修复 10+ 个函数缺少 `_not_deleted` 过滤的问题：
- `list_shots_by_scene` - 添加过滤
- `create_scene_beat` - scene/beat 查询添加过滤
- `create_shot` - scene/shot/beat 查询添加过滤
- `create_scene_with_children` - environment 查询添加过滤
- `update_scene` - scene/environment 查询添加过滤
- `update_scene_beat` - beat/conflict 查询添加过滤
- `update_shot` - shot/conflict/beat 查询添加过滤
- `seed_scenes_from_script_json` - script/existing scenes 查询添加过滤

### 硬删除改为软删除 (story_structure_service.py)

修改删除函数签名和实现：
- `delete_scene(db, scene_id, *, user_id=None, reason=None)` - 软删除场景及其子元素
- `delete_scene_beat(db, beat_id, *, user_id=None, reason=None)` - 软删除节拍
- `delete_shot(db, shot_id, *, user_id=None, reason=None)` - 软删除镜头
- `delete_environment(db, env_id, *, user_id=None, reason=None)` - 软删除环境

### 新增 business_id 查询函数 (story_structure_service.py)

- `get_scene(db, scene_id)` / `get_scene_by_business_id(db, business_id)` / `resolve_scene(db, identifier)`
- `get_shot(db, shot_id)` / `get_shot_by_business_id(db, business_id)` / `resolve_shot(db, identifier)`
- `get_scene_beat(db, beat_id)` / `get_scene_beat_by_business_id(db, business_id)` / `resolve_scene_beat(db, identifier)`

### 新增 business_id 端点

**scenes.py:**
- `GET /scenes/{scene_id}` - 按 id 获取
- `GET /scenes/business/{scene_business_id}` - 按 business_id 获取
- `PUT /scenes/business/{scene_business_id}` - 按 business_id 更新
- `DELETE /scenes/business/{scene_business_id}` - 按 business_id 删除

**shots.py:**
- `GET /shots/{shot_id}` - 按 id 获取
- `GET /shots/business/{shot_business_id}` - 按 business_id 获取
- `PUT /shots/business/{shot_business_id}` - 按 business_id 更新
- `DELETE /shots/business/{shot_business_id}` - 按 business_id 删除

**beats.py:**
- `GET /scene-beats/{beat_id}` - 按 id 获取
- `GET /scene-beats/business/{beat_business_id}` - 按 business_id 获取
- `PUT /scene-beats/business/{beat_business_id}` - 按 business_id 更新
- `DELETE /scene-beats/business/{beat_business_id}` - 按 business_id 删除

### 更新端点认证

删除端点现在需要认证以记录 `deleted_by`：
- scenes.py / shots.py / beats.py / environments.py 的 delete 端点添加 `current_user` 依赖

### 测试修复

- 更新 `test_story_structure_endpoints.py` 中的测试以包含认证 mock

## Validation

```bash
cd ai-pic-backend && python -m pytest tests/unit tests/test_story_structure_endpoints.py tests/test_story_structure_service.py -v --tb=short -q
# 结果：822 passed, 1 skipped
```

## Next Steps

1. **复合唯一约束** - 将唯一约束改为含 `is_deleted` 的复合唯一
2. **regenerate 改造** - scripts regenerate 改为"新记录 + 旧记录软删"
3. **前端 business_id** - 其余资源与深链路补齐 business_id 兜底
4. **E2E 验证** - Chrome 验证软删后列表/详情/再生成可用

## Linked Commits

- `eba067e` feat(backend): add soft delete filtering and business_id routes for story structure
