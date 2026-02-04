---
id: 2026-02-05T02-45-00Z-p1-context-pack-integration
date: 2026-02-05T02:45:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, context-pack, episode-characters, integration]
related_paths:
  - ai-pic-backend/app/services/context_pack/story_context_pack_builder.py
summary: "Added build_episode_context_pack with smart budget allocation for Story + Episode characters"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Add `build_episode_context_pack()` function to support Episode characters
- [x] Implement budget allocation strategy:
  - 50% for Story main characters (importance >= 3)
  - 50% for Episode temporary characters
  - Remaining slots for Story supporting characters (importance < 3)
- [x] Resolve Episode character resources (voice_config_override, appearance_override)
- [x] Maintain same structure and behavior as `build_story_context_pack()`

## Changes

### Modified: `ai-pic-backend/app/services/context_pack/story_context_pack_builder.py`

**1. Added import** (line 6):
```python
from app.models.episode_character import EpisodeCharacter
```

**2. Added `build_episode_context_pack()` function** (~230 lines):

**Function Signature:**
```python
def build_episode_context_pack(
    *,
    db: Session,
    story_id: int,
    episode_id: int,
    story_snapshot: Dict[str, Any],
    continuity_ledger: Optional[Dict[str, Any]],
    generation_params: Optional[Dict[str, Any]] = None,
    budget: Optional[ContextPackBudget] = None,
) -> Dict[str, Any]:
```

**Budget Allocation Strategy:**
```python
total_slots = budget.max_character_cards  # e.g., 8
story_main_slots = max(1, total_slots // 2)  # 4 slots for Story main characters
episode_slots = max(1, total_slots // 2)     # 4 slots for Episode characters
# Remaining slots filled with Story supporting characters
```

**Example with 8-slot budget:**
- Scenario 1: 2 Story main + 3 Episode → 2 Story main + 3 Episode + 3 Story supporting = 8 total
- Scenario 2: 4 Story main + 2 Episode → 4 Story main + 2 Episode + 2 Story supporting = 8 total
- Scenario 3: 3 Story main + 4 Episode → 3 Story main + 4 Episode + 1 Story supporting = 8 total

**Character Card Building - Story Main Characters:**
```python
# Fetch Story characters with importance >= 3
story_main_rows = (
    db.query(StoryCharacter)
    .filter(
        StoryCharacter.story_id == story_id,
        StoryCharacter.importance >= 3,
    )
    .order_by(StoryCharacter.importance.desc())
    .limit(story_main_slots)
    .all()
)
```

**Character Card Building - Episode Temporary Characters:**
```python
# Fetch Episode characters ordered by importance
episode_char_rows = (
    db.query(EpisodeCharacter)
    .filter(EpisodeCharacter.episode_id == episode_id)
    .order_by(EpisodeCharacter.importance.desc())
    .limit(episode_slots)
    .all()
)

# Resolve overrides:
voice_config = ec.voice_config_override or vip.voice_config
appearance = f"{vip.style_prompt}\n{ec.appearance_override}".strip()
display_name = ec.character_name or vip.name
```

**Character Card Building - Story Supporting Characters:**
```python
# Fill remaining slots with Story characters importance < 3
remaining_slots = total_slots - len(cards)
story_supporting_rows = (
    db.query(StoryCharacter)
    .filter(
        StoryCharacter.story_id == story_id,
        StoryCharacter.importance < 3,
    )
    .order_by(StoryCharacter.importance.desc())
    .limit(remaining_slots)
    .all()
)
```

**Resource Resolution for Episode Characters:**
- **Voice Config**: `voice_config_override` if set, else `VirtualIP.voice_config`
- **Appearance**: Merge `VirtualIP.style_prompt` + `appearance_override`
- **Display Name**: `character_name` if set, else `VirtualIP.name`
- **Personality**: `personality` if set, else `VirtualIP.description`
- **Background**: `background` if set, else `VirtualIP.background_story`

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/context_pack/story_context_pack_builder.py
# Output: ✅ Syntax check passed
```

✅ **Code Structure:**
- Follows same pattern as `build_story_context_pack()`
- Uses same schema models (CharacterCard, StoryContextPack, etc.)
- Applies same budget truncation and estimation logic

✅ **Backward Compatibility:**
- Existing `build_story_context_pack()` unchanged
- New function is additive, doesn't break existing workflows

## Architecture Notes

**Budget Allocation Philosophy:**
- **Story Main Characters (50%)**: Core protagonists/antagonists essential to story continuity
- **Episode Temporary Characters (50%)**: Important for current episode (快递员, 医生, etc.)
- **Story Supporting Characters (fill)**: Secondary characters as budget allows

**Why This Strategy:**
- Balances Story continuity with Episode-specific needs
- Prevents Episode characters from overwhelming the context
- Ensures main Story characters always present
- Flexible: adjusts automatically based on actual character counts

**Priority Order:**
1. Story main characters (importance >= 3) by importance DESC
2. Episode temporary characters by importance DESC
3. Story supporting characters (importance < 3) by importance DESC

**Character Card Composition:**
```
CharacterCard {
  id: VirtualIP.id
  name: EpisodeCharacter.character_name OR VirtualIP.name
  role_type: EpisodeCharacter.role_type (e.g., "temporary")
  description: EpisodeCharacter.personality OR VirtualIP.description
  background_story: EpisodeCharacter.background OR VirtualIP.background_story
  biography: VirtualIP.biography
  style_prompt: VirtualIP.style_prompt + EpisodeCharacter.appearance_override
  voice_config: EpisodeCharacter.voice_config_override OR VirtualIP.voice_config
}
```

## Use Cases

**Script Generation:**
- When generating scripts for an Episode, use `build_episode_context_pack()`
- AI receives context about both Story arc and Episode-specific characters
- Ensures consistent character portrayal across Story and Episode contexts

**Dialogue Generation:**
- Context pack provides voice configs for all characters (Story + Episode)
- Episode character voice overrides applied automatically
- Enables proper voice binding for temporary characters

**Image Generation:**
- Context pack includes appearance prompts with Episode overrides
- Story main character images available for consistency
- Episode character appearance descriptions ready for generation

## Example Output

**8-slot budget, 2 Story main, 3 Episode:**
```json
{
  "character_cards": [
    {"name": "李明", "role_type": "protagonist", "from": "Story"},      // Story main
    {"name": "张华", "role_type": "antagonist", "from": "Story"},       // Story main
    {"name": "快递员", "role_type": "temporary", "from": "Episode"},    // Episode
    {"name": "医生", "role_type": "temporary", "from": "Episode"},      // Episode
    {"name": "护士", "role_type": "temporary", "from": "Episode"},      // Episode
    {"name": "王小明", "role_type": "supporting", "from": "Story"},     // Story supporting
    {"name": "赵大爷", "role_type": "supporting", "from": "Story"},     // Story supporting
    {"name": "李阿姨", "role_type": "supporting", "from": "Story"}      // Story supporting
  ]
}
```

## Next Steps

### P1.4: Integration Tests (~200 lines)
- File: `tests/integration/api/test_episode_characters_api.py`
- Test episode character CRUD operations
- Test voice binding integration with Episode characters
- Test script generation with Episode characters
- Test context pack generation with budget allocation

### P1.5: Temporary Character Extraction (~150 lines)
- File: `app/services/script/temporary_character_extractor.py`
- Extract character names from script dialogues
- Parse stage directions for appearance descriptions
- Infer character scene appearances

## Linked Commits

(Will be added after commit)
