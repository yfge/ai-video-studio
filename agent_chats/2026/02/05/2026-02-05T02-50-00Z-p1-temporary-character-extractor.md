---
id: 2026-02-05T02-50-00Z-p1-temporary-character-extractor
date: 2026-02-05T02:50:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, script, episode-characters, extraction, auto-generation]
related_paths:
  - ai-pic-backend/app/services/script/temporary_character_extractor.py
summary: "Created temporary character extractor to parse script content for auto-generation"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Create `temporary_character_extractor.py` module
- [x] Implement `extract_temporary_characters()` function
- [x] Extract character names from script dialogues
- [x] Parse stage directions for appearance descriptions
- [x] Infer character scene appearances
- [x] Build comprehensive character information dataclass

## Changes

### Created: `ai-pic-backend/app/services/script/temporary_character_extractor.py` (~210 lines)

**1. TemporaryCharacterInfo Dataclass:**
```python
@dataclass
class TemporaryCharacterInfo:
    character_name: str              # Normalized character name
    dialogues: List[str]             # All dialogue lines
    stage_directions: List[str]      # Mentions in stage directions
    scene_appearances: List[int]     # Scene numbers
    first_appearance_scene: int      # First scene
    last_appearance_scene: int       # Last scene
    dialogue_count: int              # Total dialogue lines
    appearance_hints: List[str]      # Appearance descriptions
```

**2. Main Extraction Function:**
```python
def extract_temporary_characters(
    script_content: Dict[str, Any],
    unknown_names: Optional[List[str]] = None,
) -> List[TemporaryCharacterInfo]:
```

**Extraction Logic:**
1. **Parse Dialogues:**
   - Extract character names from dialogue.character field
   - Normalize names using `normalize_character_name_token()`
   - Filter by unknown_names if provided
   - Collect all dialogue content per character
   - Track scene appearances from dialogue.scene_number

2. **Parse Stage Directions:**
   - Search for character name mentions in stage directions
   - Use fuzzy matching to catch variations (e.g., "一个快递员", "快递员走进来")
   - Extract appearance hints using regex patterns
   - Track additional scene appearances

3. **Build Character Info:**
   - Aggregate all collected data per character
   - Calculate first/last appearance scenes
   - Count total dialogue lines
   - Sort by first appearance scene

**3. Helper Functions:**

**_fuzzy_match()**: Matches character names in text with context
```python
# Handles patterns like:
"快递员" in "一个快递员走进来"  # True
"医生" in "李医生检查病人"      # True
```

**_extract_appearance_hints()**: Extracts appearance descriptions
```python
# Regex patterns for:
- "穿着(快递制服)"      → "快递制服"
- "戴着(口罩)"          → "口罩"
- "背着(快递包)"        → "快递包"
- "拿着(医疗箱)"        → "医疗箱"
- "(年轻)的(医生)"      → "年轻医生"
```

## Use Cases

### Scenario 1: Auto-detect Unknown Characters

**Input (script_content):**
```json
{
  "dialogues": [
    {"character": "快递员", "content": "您的快递到了", "scene_number": 3},
    {"character": "快递员", "content": "请签收", "scene_number": 3},
    {"character": "医生", "content": "病人情况如何？", "scene_number": 5}
  ],
  "stage_directions": [
    {"content": "一个穿着快递制服的年轻人走进来", "scene_number": 3},
    {"content": "医生戴着听诊器检查病人", "scene_number": 5}
  ]
}

**unknown_names:** ["快递员", "医生"]
```

**Output:**
```python
[
  TemporaryCharacterInfo(
    character_name="快递员",
    dialogues=["您的快递到了", "请签收"],
    stage_directions=["一个穿着快递制服的年轻人走进来"],
    scene_appearances=[3],
    first_appearance_scene=3,
    last_appearance_scene=3,
    dialogue_count=2,
    appearance_hints=["快递制服", "年轻"]
  ),
  TemporaryCharacterInfo(
    character_name="医生",
    dialogues=["病人情况如何？"],
    stage_directions=["医生戴着听诊器检查病人"],
    scene_appearances=[5],
    first_appearance_scene=5,
    last_appearance_scene=5,
    dialogue_count=1,
    appearance_hints=["听诊器"]
  )
]
```

### Scenario 2: Extract All Characters

**Input:** Same script_content, `unknown_names=None`

**Behavior:** Extracts information for ALL characters in the script (not just unknown ones)

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/script/temporary_character_extractor.py
# Output: ✅ Syntax check passed
```

✅ **Code Quality:**
- Well-documented with docstrings
- Type hints for all functions
- Defensive programming (None checks, type checks)
- Efficient: Single pass through dialogues and stage directions

## Integration Points

**Will be used by Auto Character Creator (P1.7):**
```python
# In auto_character_creator.py
from app.services.script.temporary_character_extractor import (
    extract_temporary_characters
)

# After script generation
unknown_chars = script_result.get("unknown_names", [])
if unknown_chars:
    char_info = extract_temporary_characters(script_content, unknown_chars)
    for info in char_info:
        # Use info to create EpisodeCharacter with AI-generated background
        create_episode_character(info)
```

**Extracted Data Used For:**
1. **AI Background Generation (P1.6):**
   - `dialogues` → Infer personality from speech patterns
   - `appearance_hints` → Generate appearance_override
   - `scene_appearances` → Context for role in story

2. **EpisodeCharacter Creation:**
   - `character_name` → EpisodeCharacter.character_name
   - `scene_appearances` → EpisodeCharacter.scene_appearances (JSON)
   - `first_appearance_scene` → EpisodeCharacter.first_appearance_scene
   - `last_appearance_scene` → EpisodeCharacter.last_appearance_scene
   - `dialogue_count` → Used to infer importance level

## Example Regex Patterns

**Appearance Hints Extraction:**
```
"一个穿着快递制服的年轻人"
  → "快递制服" (from "穿着(快递制服)")
  → "年轻" (from "(年轻)的(人)")

"戴着口罩背着医疗箱的医生"
  → "口罩" (from "戴着(口罩)")
  → "医疗箱" (from "背着(医疗箱)")
```

**Fuzzy Character Matching:**
```
char_name="快递员", text="一个快递员走进来"
  → Match via pattern "一个" + char_name

char_name="医生", text="李医生检查病人"
  → Match via direct substring

char_name="护士", text="护士站在病床旁"
  → Match via pattern char_name + "站"
```

## Next Steps

### P1.6: AI Character Background Generator (~120 lines)
- File: `app/services/script/character_background_generator.py`
- Function: `generate_character_background()`
- Input: TemporaryCharacterInfo
- Output: personality, background, appearance_override
- Uses AI to analyze dialogues and generate character profile

### P1.7: Auto Character Creator Service (~200 lines)
- File: `app/services/script/auto_character_creator.py`
- Function: `auto_create_episode_characters()`
- Orchestrates: Extraction → AI Generation → EpisodeCharacter creation
- Returns: List of created EpisodeCharacter records

## Linked Commits

(Will be added after commit)
