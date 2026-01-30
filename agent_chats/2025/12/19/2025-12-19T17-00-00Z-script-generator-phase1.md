---
id: 2025-12-19T17-00-00Z-script-generator-phase1
date: 2025-12-19T17:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, ai-generation, phase1]
related_paths:
  - ai-pic-backend/app/services/script/__init__.py
  - ai-pic-backend/app/services/script/script_generator.py
  - ai-pic-backend/app/services/script/script_utils.py
  - ai-pic-backend/tests/unit/services/script/test_script_generator.py
summary: "Create ScriptGenerator for AI-powered script creation [Phase 1 Task 1.1.3]"
---

## User Prompt

Continue with refactoring plan Phase 1, Task 1.1.3: Create Script Generation Service.

## Goals

1. Create ScriptGenerator class for AI-powered script generation
2. Extract utility functions to script_utils.py module
3. Handle prompt building, AI service calls, and content normalization
4. Add unit tests for generator methods
5. Keep files under size limits per AGENTS.md

## Changes

### New Files

1. `ai-pic-backend/app/services/script/script_utils.py` (~210 lines)

   - `to_int()`: Safe integer conversion
   - `collect_previous_episode_summaries()`: Gather episode context
   - `build_character_profiles()`: Build character data
   - `build_episode_data()`: Build episode context
   - `extract_episode_scenes()`: Extract scenes from metadata
   - `build_story_data()`: Build story context

2. `ai-pic-backend/app/services/script/script_generator.py` (~295 lines)

   - `ScriptGenerator` class with:
     - `generate_script()`: Main AI generation method
     - `preview_prompt()`: Preview prompt without AI call
     - `_build_context()`: Build story/episode context
     - `_parse_ai_result()`: Parse AI response
     - `_normalize_content()`: Normalize AI content
     - `_normalize_scenes/dialogues/stage_directions()`: Normalize parts
     - `_build_extra_metadata()`: Build metadata dict

3. `ai-pic-backend/tests/unit/services/script/test_script_generator.py` (~170 lines)
   - 17 unit tests covering all methods
   - Tests for normalization edge cases
   - Tests for error handling

### Modified Files

1. `ai-pic-backend/app/services/script/__init__.py`
   - Added exports for ScriptGenerator and get_script_generator

## Validation

```bash
# Import test
python -c "from app.services.script import ScriptGenerator, get_script_generator; print('Import successful')"
# Output: Import successful

# Unit tests
pytest tests/unit/services/script/test_script_generator.py -v
# Output: 17 passed
```

## Next Steps

1. Task 1.1.4: Split scripts.py CRUD endpoints to use ScriptService
2. Task 1.1.5: Split scripts.py generation endpoints to use ScriptGenerator
3. Continue with remaining Phase 1 tasks

## Linked Commits

- Pending: This entry will be committed with the generator implementation
