---
id: 2025-12-24T18-30-00Z-enhance-timeline-agent-context
date: 2025-12-24T18:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, timeline-agent, context-enhancement]
related_paths:
  - ai-pic-backend/app/services/dialogue_audio_service.py
  - ai-pic-backend/app/services/timeline_agent/agent.py
  - ai-pic-backend/app/services/timeline_agent/schemas.py
  - ai-pic-backend/app/services/timeline_agent/utils.py
summary: "Enhance timeline agent with richer scene context for better timing decisions"
---

## User Prompt

User requested: "现在检查所有的agent 看是否已经传入了必要的上下文"

## Goals

1. Audit all LangGraph agents for proper context passing
2. Identify and fix any missing context
3. Ensure agents have access to necessary data for quality output

## Agent Analysis

| Agent                       | Context Passed                                     | Status      |
| --------------------------- | -------------------------------------------------- | ----------- |
| **StoryLangGraphAgent**     | title, genre, characters, theme, setting           | ✅ Complete |
| **EpisodeLangGraphAgent**   | story (full), episode params, focus_characters     | ✅ Complete |
| **ScriptLangGraphAgent**    | episode, story (with characters), format/style     | ✅ Complete |
| **StoryboardReActReasoner** | script (full with scenes, dialogues)               | ✅ Complete |
| **TimelineLangGraphAgent**  | dialogues, stage_directions, limited scene_context | ⚠️ Enhanced |

## Changes

### Backend

**`ai-pic-backend/app/services/dialogue_audio_service.py`**

Enhanced scene_context passed to timeline agent:

```python
scene_context = {
    "scene_id": scene.id,
    "scene_number": scene_number,
    "slug_line": getattr(scene, "slug_line", None),
    "location": getattr(scene, "location", None),
    "time_of_day": getattr(scene, "time_of_day", None),
    "summary": getattr(scene, "summary", None),
    "primary_characters": getattr(scene, "primary_characters", None),
    "conflict_notes": getattr(scene, "conflict_notes", None),
    "dramatic_question": None,  # from step_outline
}
```

**`ai-pic-backend/app/services/timeline_agent/schemas.py`**

Added new fields to SceneContext:

- `slug_line` - Scene slug line (e.g., "INT. APARTMENT - NIGHT")
- `location` - Scene location
- `time_of_day` - Time of day
- `summary` - Scene description

**`ai-pic-backend/app/services/timeline_agent/utils.py`**

Updated `build_scene_context()` to accept and use new fields:

- Now accepts slug_line, location, time_of_day, summary, primary_characters
- Merges primary_characters with dialogue-extracted characters

**`ai-pic-backend/app/services/timeline_agent/agent.py`**

- Updated `_analyze_scene()` to pass new context fields
- Enhanced `_build_reasoning_prompt()` to include scene description and location in prompt
- Added consideration for scene atmosphere in timing decisions

## Validation

1. Import test: All timeline agent components import successfully
2. SceneContext schema accepts new fields
3. build_scene_context correctly merges character sources

## Next Steps

1. Monitor timeline quality improvements with enhanced context
2. Consider adding more scene metadata (e.g., camera notes) if needed

## Linked Commits

- 718d5bc feat(backend): enhance timeline agent with richer scene context
