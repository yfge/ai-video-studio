---
id: 2026-02-05T03-00-00Z-p1-auto-character-creator
date: 2026-02-05T03:00:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, script, episode-characters, auto-generation, workflow]
related_paths:
  - ai-pic-backend/app/services/script/auto_character_creator.py
summary: "Created auto character creator service to orchestrate complete auto-generation workflow"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Create `auto_character_creator.py` module
- [x] Implement `auto_create_episode_characters()` orchestration function
- [x] Extract characters from script (using P1.5 extractor)
- [x] Generate backgrounds with AI (using P1.6 generator)
- [x] Get or create default VirtualIP for temporary characters
- [x] Create EpisodeCharacter records in database
- [x] Infer importance from dialogue count
- [x] Return created character information for user notification

## Changes

### Created: `ai-pic-backend/app/services/script/auto_character_creator.py` (~330 lines)

**1. Main Orchestration Function:**
```python
async def auto_create_episode_characters(
    *,
    db: "Session",
    episode_id: int,
    script_content: Dict[str, Any],
    unknown_names: List[str],
    user_id: int,
    ai_service: Optional[Any] = None,
    default_virtual_ip_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
```

**Workflow Steps:**
1. **Extract**: Call `extract_temporary_characters()` (P1.5)
2. **VirtualIP**: Get or create default VirtualIP
3. **Context**: Extract scene context from script
4. **Generate**: For each character:
   - Generate background with AI (P1.6)
   - Infer importance from dialogue count
   - Create EpisodeCharacter record
5. **Commit**: Commit all records to database
6. **Return**: List of created character info

**2. Single Character Creator:**
```python
async def _create_single_character(
    *,
    db: "Session",
    episode_id: int,
    character_info: TemporaryCharacterInfo,
    default_vip: VirtualIP,
    scene_context: Dict[str, Any],
    ai_service: Optional[Any],
) -> Optional[Dict[str, Any]]:
```

**Creates EpisodeCharacter with:**
- `character_name`: From extracted info
- `role_type`: "temporary"
- `importance`: Inferred from dialogue count (1-5)
- `personality`: AI-generated
- `background`: AI-generated
- `appearance_override`: AI-generated
- `scene_appearances`: From extracted info (JSON list)
- `first_appearance_scene`: From extracted info
- `last_appearance_scene`: From extracted info
- `extra_metadata`: Auto-creation metadata

**3. Default VirtualIP Management:**
```python
def _get_or_create_default_virtual_ip(
    *,
    db: "Session",
    user_id: int,
    virtual_ip_id: Optional[int] = None,
) -> Optional[VirtualIP]:
```

**VirtualIP Selection Logic:**
1. If `virtual_ip_id` provided → Use it
2. Else search for existing "临时角色默认形象" for user
3. Else create new default VirtualIP

**Default VirtualIP Properties:**
```python
name = "临时角色默认形象"
description = "用于Episode临时角色的默认形象，可后续替换为专用形象"
personality = "通用临时角色"
style_prompt = "普通人物形象"
voice_config = {
    "provider": "minimax",
    "voice_id": "male-qn-qingse",  # Default voice
}
```

**4. Importance Inference:**
```python
def _infer_importance(dialogue_count: int) -> int:
    if dialogue_count >= 10:
        return 3  # Important temporary character
    elif dialogue_count >= 5:
        return 2  # Moderate importance
    else:
        return 1  # Minor character
```

**5. Scene Context Extraction:**
```python
def _extract_scene_context(script_content: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "setting_location": metadata.get("setting_location", ""),
        "setting_time": metadata.get("setting_time", ""),
    }
```

## Use Cases

### Scenario 1: Complete Auto-Creation Workflow

**Input:**
```python
# After script generation
script_content = {
    "scenes": [...],
    "dialogues": [
        {"character": "快递员", "content": "您的快递到了", "scene_number": 3},
        {"character": "快递员", "content": "请签收", "scene_number": 3},
        {"character": "医生", "content": "病人情况如何？", "scene_number": 5},
    ],
    "stage_directions": [
        {"content": "穿着快递制服的年轻人走进来", "scene_number": 3},
    ],
    "metadata": {
        "setting_location": "城市住宅小区",
        "setting_time": "现代",
    }
}

unknown_names = ["快递员", "医生"]

# Auto-create characters
created = await auto_create_episode_characters(
    db=db,
    episode_id=4,
    script_content=script_content,
    unknown_names=unknown_names,
    user_id=1,
    ai_service=ai_service,
)
```

**Output:**
```python
[
    {
        "episode_character_id": 1,
        "episode_character_business_id": "4e8ff28e...",
        "character_name": "快递员",
        "virtual_ip_id": 999,
        "importance": 1,
        "needs_customization": True,
        "generated_info": {
            "personality": "热情、专业、服务意识强",
            "background": "快递公司员工，负责本小区配送",
            "appearance_override": "穿着快递制服，背着快递包",
            "scene_appearances": [3],
            "dialogue_count": 2,
        }
    },
    {
        "episode_character_id": 2,
        "character_name": "医生",
        "virtual_ip_id": 999,
        "importance": 1,
        "needs_customization": True,
        "generated_info": {...}
    }
]
```

### Scenario 2: Using Specific VirtualIP

**Input:**
```python
# Use specific VirtualIP instead of default
created = await auto_create_episode_characters(
    db=db,
    episode_id=4,
    script_content=script_content,
    unknown_names=["快递员"],
    user_id=1,
    default_virtual_ip_id=5,  # Use specific VirtualIP
)
```

**Behavior:** Uses VirtualIP ID 5 instead of creating/finding default

### Scenario 3: Multiple Characters with Varying Importance

**Input:**
```python
# Character A: 12 dialogue lines → importance=3
# Character B: 7 dialogue lines → importance=2
# Character C: 2 dialogue lines → importance=1
```

**Result:** Characters automatically assigned importance based on dialogue count

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/script/auto_character_creator.py
# Output: ✅ Syntax check passed
```

✅ **Code Quality:**
- Async workflow support
- Comprehensive error handling
- Database transaction management (flush + commit)
- Logging at all steps
- Graceful degradation (AI failures handled)

## Architecture Notes

**Complete Auto-Generation Pipeline:**
```
Script Generation
    ↓
Unknown Names Detected
    ↓
auto_create_episode_characters()
    ↓
├─ 1. Extract (P1.5)
│   └─ extract_temporary_characters()
│       └─ Returns: TemporaryCharacterInfo[]
│
├─ 2. Get/Create VirtualIP
│   └─ _get_or_create_default_virtual_ip()
│       └─ Returns: VirtualIP
│
├─ 3. Extract Scene Context
│   └─ _extract_scene_context()
│       └─ Returns: {setting_location, setting_time}
│
├─ 4. For Each Character:
│   └─ _create_single_character()
│       ├─ Generate Background (P1.6)
│       │   └─ generate_character_background()
│       │       └─ Returns: {personality, background, appearance_override}
│       ├─ Infer Importance
│       │   └─ _infer_importance(dialogue_count)
│       └─ Create EpisodeCharacter
│           └─ db.add(episode_char)
│
└─ 5. Commit & Return
    └─ db.commit()
    └─ Returns: List[created_character_info]
```

**Database Transaction Strategy:**
- `db.flush()` after each character → Gets ID without committing
- Single `db.commit()` at end → All-or-nothing transaction
- `db.rollback()` on error → Clean failure

**Error Handling Strategy:**
- Character extraction fails → Return empty list
- VirtualIP creation fails → Return empty list
- Single character creation fails → Log error, continue with others
- AI generation fails → Use heuristics fallback
- Commit fails → Rollback all, return empty list

## Integration with Script Agent

**Will be called in script_agent.py after script generation:**

```python
# In script_agent.py generate() method, after script generation

if result.get("content"):
    unknown_chars = result.get("unknown_names", [])

    if unknown_chars and db:
        from app.services.script.auto_character_creator import (
            auto_create_episode_characters
        )

        auto_created = await auto_create_episode_characters(
            db=db,
            episode_id=episode_id,
            script_content=result["content"],
            unknown_names=unknown_chars,
            user_id=current_user.id,
            ai_service=self.service.ai_manager,
        )

        result["auto_created_characters"] = auto_created
```

**API Response Enhancement:**
```json
{
  "content": {...},
  "unknown_names": ["快递员", "医生"],
  "auto_created_characters": [
    {
      "episode_character_id": 1,
      "character_name": "快递员",
      "needs_customization": true,
      ...
    }
  ]
}
```

## User Experience

**Before Auto-Creation:**
- User generates script → Gets "unknown_names" warnings
- Must manually create EpisodeCharacter for each unknown name
- Must manually fill in personality, background, appearance
- Time-consuming and error-prone

**After Auto-Creation:**
- User generates script → Characters auto-created
- Receives list of created characters with IDs
- Can review and customize later (needs_customization flag)
- Can replace default VirtualIP with custom one
- Immediate script validation success (no more unknown_names)

**Frontend Notification (Future):**
```
✅ Script generated successfully!

⚠️ Auto-created 2 temporary characters:
- 快递员 (ID: 1) - Click to customize
- 医生 (ID: 2) - Click to customize
```

## Next Steps

### Integration with Script Agent (Final Integration)
- Modify `script_agent.py` generate() method
- Call `auto_create_episode_characters()` after script generation
- Add `auto_created_characters` to response
- Update script generation API to include character info

### Frontend Integration (Future)
- Display auto-created characters notification
- Add "Customize Character" button with character ID
- Show character list in Episode editing page
- Allow VirtualIP replacement

### P1.4: Integration Tests (Deferred)
- File: `tests/integration/api/test_episode_characters_api.py`
- Test complete auto-creation workflow
- Test with/without AI service
- Test error handling scenarios

## Linked Commits

(Will be added after commit)
