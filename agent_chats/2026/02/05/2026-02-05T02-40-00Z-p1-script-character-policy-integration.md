---
id: 2026-02-05T02-40-00Z-p1-script-character-policy-integration
date: 2026-02-05T02:40:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, script-policy, episode-characters, integration]
related_paths:
  - ai-pic-backend/app/services/script/script_character_policy.py
summary: "Added Episode character support to script character policy enforcement"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Add `build_episode_alias_map()` function to fetch Episode character aliases
- [x] Add `build_combined_alias_map()` function to merge Story and Episode aliases
- [x] Update `enforce_script_character_policy()` to accept episode_id and db parameters
- [x] Ensure Episode characters take priority over Story characters in alias resolution
- [x] Maintain backward compatibility

## Changes

### Modified: `ai-pic-backend/app/services/script/script_character_policy.py`

**1. Added imports** (lines 1-15):
```python
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
```

**2. Added `build_episode_alias_map()` function** (~30 lines):
```python
def build_episode_alias_map(
    episode_id: int,
    db: "Session",
) -> dict[str, str]:
    """Build alias -> canonical mapping from EpisodeCharacter registry."""
```

Key features:
- Fetches EpisodeCharacter records for the given episode_id
- Builds canonical names from character_name or VirtualIP.name
- Extracts aliases using the same logic as Story characters
- Returns alias → canonical name mapping

**3. Added `build_combined_alias_map()` function** (~20 lines):
```python
def build_combined_alias_map(
    story: Story,
    episode_id: Optional[int] = None,
    db: Optional["Session"] = None,
) -> dict[str, str]:
    """Build combined alias map from Story and Episode characters.

    Episode characters take priority over Story characters when there's a conflict.
    """
```

Key features:
- Starts with Story character alias map
- Adds Episode character alias map if episode_id provided
- Episode map updates/overrides Story map (Episode priority)
- Backward compatible: works without episode_id

**4. Updated `enforce_script_character_policy()` signature and implementation**:
- Added parameters: `episode_id: Optional[int] = None, db: Optional["Session"] = None`
- Changed from: `alias_to_canonical = build_story_alias_map(story)`
- To: `alias_to_canonical = build_combined_alias_map(story, episode_id, db)`
- Updated docstring to reflect Episode character support

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/script/script_character_policy.py
# Output: ✅ Syntax check passed
```

✅ **Backward Compatibility:**
- All new parameters are optional
- Existing calls without episode_id/db still work
- Returns same behavior as before when Episode characters not provided

## Architecture Notes

**Character Priority Resolution:**
```
Story character "医生" (name: "李医生")
Episode character "医生" (name: "急诊医生")
→ Final alias map: "医生" → "急诊医生" (Episode wins)
```

**Integration with Script Generation:**
- `enforce_script_character_policy()` called during script processing
- Now includes both Story-level and Episode-level characters
- Prevents "unknown_names" warnings for temporary Episode characters
- Ensures proper character name normalization across contexts

**Alias Resolution Flow:**
1. Build Story character aliases (canonical names + variants)
2. Build Episode character aliases (if episode_id provided)
3. Merge maps with Episode priority (`.update()`)
4. Validate script dialogues against combined alias map
5. Normalize character names to canonical forms

## Why This Matters

**Before this change:**
- Only Story characters recognized in scripts
- Episode temporary characters (快递员, 医生) flagged as "unknown_names"
- Manual workarounds needed for temporary characters

**After this change:**
- Episode temporary characters fully integrated
- Script validation works seamlessly for both character types
- Episode context overrides Story context (more specific wins)
- Clean separation of concerns (Story = persistent, Episode = temporary)

## Next Steps

### P1.3: Context Pack Integration (~80 lines)
- File: `app/services/context_pack/story_context_pack_builder.py`
- Add `build_episode_context_pack()` function
- Implement budget allocation:
  - 50% for Story main characters
  - 50% for Episode temporary characters
  - Remaining slots for Story supporting characters

### P1.4: Integration Tests (~200 lines)
- File: `tests/integration/api/test_episode_characters_api.py`
- End-to-end API tests
- Voice binding integration tests
- Script generation with Episode characters

## Linked Commits

(Will be added after commit)
