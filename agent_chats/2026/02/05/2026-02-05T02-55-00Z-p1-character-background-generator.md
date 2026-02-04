---
id: 2026-02-05T02-55-00Z-p1-character-background-generator
date: 2026-02-05T02:55:00Z
participants: [human, claude-sonnet-4.5]
models: [claude-sonnet-4-5-20250929]
tags: [backend, script, episode-characters, ai-generation, auto-generation]
related_paths:
  - ai-pic-backend/app/services/script/character_background_generator.py
summary: "Created AI-powered character background generator with heuristic fallback"
---

## User Prompt

依次实现计划，每完成一项以后就进行一个原子化提交，有问题及时处理和解决，不要停下来问 直到所有计划工作都完成

## Goals

- [x] Create `character_background_generator.py` module
- [x] Implement `generate_character_background()` function
- [x] Build AI prompt from character dialogues and context
- [x] Add AI-powered generation (async)
- [x] Add heuristic fallback for common character types
- [x] Generate personality, background, and appearance descriptions

## Changes

### Created: `ai-pic-backend/app/services/script/character_background_generator.py` (~270 lines)

**1. Main Generation Function:**
```python
async def generate_character_background(
    *,
    character_info: TemporaryCharacterInfo,
    scene_context: Dict[str, Any],
    ai_service: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Returns:
      - personality: e.g., "热情、专业、认真负责"
      - background: e.g., "快递公司员工，负责本小区配送"
      - appearance_override: e.g., "穿着快递制服，背着快递包"
    """
```

**2. AI Prompt Builder:**
```python
def _build_generation_prompt(
    character_info: TemporaryCharacterInfo,
    scene_context: Dict[str, Any],
) -> str:
```

**Prompt Structure:**
```
请根据以下信息生成临时角色的详细背景资料：

角色名称：快递员
出场场景：第3场景到第3场景
对白总数：2句

角色对白示例：
"您的快递到了"
"请签收"

外观线索：快递制服, 年轻

场景设定：
- 地点：城市住宅小区
- 时代：现代

请生成以下三个方面的描述：
1. 性格特点（personality）：基于对白分析...
2. 角色背景（background）：1-2句话描述...
3. 外观描述（appearance_override）：1-2句话描述...

请以JSON格式返回：
{
  "personality": "...",
  "background": "...",
  "appearance_override": "..."
}
```

**3. AI-Powered Generation:**
```python
async def _generate_with_ai(
    prompt: str,
    ai_service: Any,
) -> Dict[str, str]:
```

Features:
- Async AI service call
- JSON response parsing
- Error handling with fallback to heuristics
- Temperature 0.7 for creative but consistent output
- Max 500 tokens for concise descriptions

**4. Heuristic Fallback System:**
```python
def _generate_with_heuristics(
    character_info: TemporaryCharacterInfo,
) -> Dict[str, str]:
```

**Pre-defined Character Templates:**
```python
role_hints = {
    "快递员": {
        "personality": "热情、负责、有耐心",
        "background": "快递公司员工，负责配送工作",
        "appearance": "穿着快递制服，背着快递包",
    },
    "医生": {
        "personality": "专业、冷静、细心",
        "background": "医疗工作者，负责诊疗工作",
        "appearance": "穿着白大褂，戴着听诊器",
    },
    "护士": {...},
    "警察": {...},
    "服务员": {...},
    "司机": {...},
}
```

**Matching Logic:**
1. Exact match: "快递员" → Use template
2. Partial match: "李医生" → Match "医生" template
3. Generic fallback: Unknown role → Generic template with appearance hints

## Use Cases

### Scenario 1: AI Generation (Success)

**Input:**
```python
character_info = TemporaryCharacterInfo(
    character_name="快递员",
    dialogues=["您的快递到了", "请签收"],
    appearance_hints=["快递制服", "年轻"],
    dialogue_count=2,
    ...
)
scene_context = {
    "setting_location": "城市住宅小区",
    "setting_time": "现代"
}
ai_service = AIService(...)
```

**AI Output:**
```json
{
  "personality": "热情、专业、服务意识强",
  "background": "本地快递公司员工，负责该小区的日常配送，熟悉小区环境和住户",
  "appearance_override": "穿着蓝色快递制服，背着大号快递包，看起来年轻有活力"
}
```

### Scenario 2: Heuristic Fallback (AI Failed or Unavailable)

**Input:** Same as above, `ai_service=None`

**Heuristic Output:**
```json
{
  "personality": "热情、负责、有耐心",
  "background": "快递公司员工，负责配送工作",
  "appearance_override": "穿着快递制服，背着快递包"
}
```

### Scenario 3: Unknown Role with Appearance Hints

**Input:**
```python
character_info = TemporaryCharacterInfo(
    character_name="保安大叔",
    dialogues=["请出示证件", "这里禁止进入"],
    appearance_hints=["保安制服", "年长"],
    ...
)
ai_service = None
```

**Output:**
```json
{
  "personality": "普通、友好、礼貌",
  "background": "保安大叔，在剧情中扮演临时角色",
  "appearance_override": "保安制服, 年长"
}
```

## Validation

✅ **Syntax Check:**
```bash
python -m py_compile app/services/script/character_background_generator.py
# Output: ✅ Syntax check passed
```

✅ **Code Quality:**
- Async support for AI service integration
- Graceful degradation (AI → Heuristics)
- Comprehensive error handling
- Pre-defined templates for common roles
- Flexible prompt building

## Architecture Notes

**AI vs. Heuristics Decision Tree:**
```
generate_character_background()
    ├─ ai_service provided?
    │   ├─ Yes → _generate_with_ai()
    │   │       ├─ Success → Return AI result
    │   │       └─ Fail → _generate_with_heuristics()
    │   └─ No → _generate_with_heuristics()
    │           ├─ Exact match → Use template
    │           ├─ Partial match → Use template
    │           └─ No match → Generic + appearance hints
```

**Why Heuristic Fallback:**
- Reliability: Works even without AI service
- Cost: Saves AI API calls for common characters
- Speed: Instant response for known roles
- Quality: Pre-defined templates are high-quality

**Why AI Generation:**
- Contextual: Analyzes actual dialogues
- Creative: Generates unique descriptions
- Adaptive: Handles unusual character types
- Rich: More detailed and nuanced descriptions

## Integration with Auto Creator (P1.7)

**Will be called by auto_character_creator.py:**
```python
from app.services.script.character_background_generator import (
    generate_character_background
)

# For each extracted character
for char_info in extracted_characters:
    # Generate background with AI
    background = await generate_character_background(
        character_info=char_info,
        scene_context=scene_context,
        ai_service=ai_service,
    )

    # Use generated data to create EpisodeCharacter
    episode_char = EpisodeCharacter(
        character_name=char_info.character_name,
        personality=background["personality"],
        background=background["background"],
        appearance_override=background["appearance_override"],
        ...
    )
```

## Next Steps

### P1.7: Auto Character Creator Service (~200 lines)
- File: `app/services/script/auto_character_creator.py`
- Orchestrate complete auto-creation workflow:
  1. Extract characters from script (P1.5)
  2. Generate backgrounds with AI (P1.6)
  3. Assign default VirtualIP
  4. Create EpisodeCharacter records in database
  5. Return created characters list

- Integration point: Called after script generation in script_agent.py
- User notification: Return auto-created characters in script response

## Linked Commits

(Will be added after commit)
