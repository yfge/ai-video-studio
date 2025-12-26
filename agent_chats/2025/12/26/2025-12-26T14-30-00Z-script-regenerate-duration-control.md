---
id: 2025-12-26T14-30-00Z-script-regenerate-duration-control
date: 2025-12-26T14:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, duration-control, script-regeneration]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py
summary: "Added scene_budgets support to script regeneration for duration control"
---

## User Prompt

User requested to fix the script regeneration flow to support duration control ("修改"). The previous session identified that `_build_script_regenerate_request` did NOT include `duration_minutes` from episode, and `_process_script_regeneration_task` did NOT pass `scene_budgets` to `ai_service.generate_script()`.

## Goals

1. Add `scene_budgets` parameter to `ai_service.generate_script()` and pass through to `script_agent.generate()`
2. Modify `_build_script_regenerate_request` to include `duration_minutes` from episode
3. Modify `_process_script_regeneration_task` to compute and pass `scene_budgets` based on `duration_minutes`

## Changes

### 1. ai_service.py - Added scene_budgets parameter

**`ai-pic-backend/app/services/ai_service.py` (line 1097-1128)**:

Added `scene_budgets: Optional[List["SceneBudget"]] = None` parameter to `generate_script()` and pass it through to `script_agent.generate()`:

```python
async def generate_script(
    self,
    ...
    scene_budgets: Optional[List["SceneBudget"]] = None,
) -> Optional[Dict[str, Any]]:
    """基于剧集信息生成详细剧本"""
    if self.script_agent:
        try:
            lg = await self.script_agent.generate(
                ...
                scene_budgets=scene_budgets,
            )
```

### 2. scripts_legacy.py - _build_script_regenerate_request

**`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py` (line 3735-3753)**:

Added `duration_minutes` to the request dictionary:

```python
def _build_script_regenerate_request(
    script: Script, episode: Episode, override_model: Optional[str] = None
) -> Dict[str, Any]:
    original_params = script.generation_params or {}
    # 获取剧集目标时长（分钟）
    duration_minutes = getattr(episode, "duration_minutes", None)
    return {
        ...
        "duration_minutes": duration_minutes,
    }
```

### 3. scripts_legacy.py - _process_script_regeneration_task

**`ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py` (line 1461-1503)**:

Added scene budget computation before calling `ai_service.generate_script()`:

```python
# 计算场景预算（如果有 duration_minutes）
scene_budgets = None
duration_minutes = request_dict.get("duration_minutes")
if duration_minutes and duration_minutes > 0:
    scenes = episode_data.get("scenes", [])
    if scenes:
        from app.services.duration_orchestrator.utils import allocate_scene_budgets
        try:
            scene_budgets, _ = allocate_scene_budgets(
                total_duration_minutes=duration_minutes,
                scenes=scenes,
            )
            logger.info(
                "剧本重新生成: 分配场景预算",
                extra={
                    "script_id": script_id,
                    "duration_minutes": duration_minutes,
                    "scene_count": len(scene_budgets),
                },
            )
        except Exception as e:
            logger.warning(f"分配场景预算失败: {e}")

# ... in _run():
return await ai_service.generate_script(
    ...
    scene_budgets=scene_budgets,
)
```

## Validation

1. **Import Check**: Both modified modules import successfully
   ```bash
   python -c "from app.api.v1.endpoints.scripts_legacy import _build_script_regenerate_request; print('OK')"
   python -c "from app.services.ai_service import AIService; print('OK')"
   ```

2. **Unit Tests**: All script agent word count tests pass
   ```bash
   pytest tests/unit/services/test_script_agent_word_count.py -v
   # 7 passed
   ```

## Next Steps

1. When a script is regenerated, if the episode has `duration_minutes` set, the system will:
   - Compute `scene_budgets` based on `duration_minutes` and episode scenes
   - Pass `scene_budgets` to `script_agent.generate()` which builds word count constraints in the prompt
   - This ensures regenerated scripts have dialogue content sized appropriately for the target duration

2. End-to-end validation needed:
   - Trigger a script regeneration for an episode with `duration_minutes=3`
   - Verify logs show "剧本重新生成: 分配场景预算"
   - Verify generated script has richer dialogue content

## Linked Commits

- `b314db7` feat(duration-control): add scene_budgets support to script regeneration
- (pending) fix(duration-control): improve budget allocation with buffer and density factors
