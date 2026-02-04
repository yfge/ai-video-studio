---
id: 2026-02-05T02-35-00Z-p1-script-agent-integration
date: 2026-02-05T02:35:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, script-agent, episode-characters, integration]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
summary: "Integrated Episode character validation into Script Agent"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Update `_validate_script_characters` method to include Episode temporary characters
- [x] Pass `episode_id` and `db` parameters from `generate` method to `_validate_script_characters`
- [x] Ensure backward compatibility (episode_id and db are optional)
- [x] Validate changes with syntax check

## Changes

### Modified: `ai-pic-backend/app/services/script_agent.py`

**1. Updated `_validate_script_characters` method signature** (line 86):
- Added optional parameters: `episode_id: Optional[int] = None` and `db: Optional["Session"] = None`
- Method now accepts Episode context for character validation

**2. Added Episode character fetching logic** (inside `_validate_script_characters`):
```python
if episode_id and db:
    try:
        from app.models.episode_character import EpisodeCharacter
        from app.models.virtual_ip import VirtualIP

        episode_chars = (
            db.query(EpisodeCharacter)
            .filter(
                EpisodeCharacter.episode_id == episode_id,
                EpisodeCharacter.is_deleted == False,
            )
            .all()
        )

        for ec in episode_chars:
            display_name = ec.character_name or ec.virtual_ip.name if ec.virtual_ip else f"临时角色{ec.id}"
            alias_map[normalize_name(display_name)] = display_name

            profile = {
                "id": ec.id,
                "name": display_name,
                "personality": ec.personality or (ec.virtual_ip.personality if ec.virtual_ip else None),
                "background": ec.background or (ec.virtual_ip.background if ec.virtual_ip else None),
                "role": "temporary",
            }
            profiles.append(profile)
```

**3. Updated `generate` method** (line 647):
- Already had `db: Optional["Session"] = None` parameter added in previous work

**4. Updated call site** (line 1336):
- Changed from: `char_validation = self._validate_script_characters(content, story_characters)`
- To: `char_validation = self._validate_script_characters(content, story_characters, episode.get("id"), db)`

**Integration Logic:**
- When both `episode_id` and `db` are provided, fetches EpisodeCharacter records for the episode
- Builds character profiles for Episode temporary characters (delivery person, doctor, etc.)
- Adds them to the alias map and validation profiles
- Episode characters are validated alongside Story characters
- Backward compatible: if episode_id or db is None, only Story characters are validated

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/script_agent.py
# Output: ✅ Syntax check passed
```

✅ **Unit Tests:**
```bash
pytest tests/unit/test_episode_character_service.py -v
# Result: 8 passed, all tests pass
```

✅ **Backward Compatibility:**
- Optional parameters ensure existing calls without episode_id/db still work
- No changes required to other call sites

## Architecture Notes

**Integration Pattern:**
- Script Agent now validates both Story-level characters and Episode-level temporary characters
- Episode characters are fetched on-demand when episode_id is provided
- Character profiles merged before validation, ensuring consistent character naming in scripts

**Character Validation Flow:**
1. Story characters added to profiles (always)
2. Episode characters fetched and added to profiles (when episode_id provided)
3. Script dialogues validated against combined character list
4. Unknown character names reported as warnings

**Why This Matters:**
- Scripts can now reference temporary characters (快递员, 医生, etc.) without "unknown_names" warnings
- Validation ensures character consistency across Story and Episode contexts
- Enables proper voice binding for temporary characters in dialogue generation

## Next Steps

### P1.2: Script Character Policy Integration (~50 lines)
- File: `app/services/script/script_character_policy.py`
- Add `build_episode_alias_map()` function
- Update `enforce_script_character_policy()` to use combined alias map

### P1.3: Context Pack Integration (~80 lines)
- File: `app/services/context_pack/story_context_pack_builder.py`
- Add `build_episode_context_pack()` function
- Implement budget allocation (50% Story主角 + 50% Episode临时角色)

### P1.4: Integration Tests (~200 lines)
- File: `tests/integration/api/test_episode_characters_api.py`
- End-to-end API tests
- Voice binding integration tests

## Linked Commits

(Will be added after commit)
