---
id: 2026-02-04T08-30-00Z-p2-context-injection
date: 2026-02-04T08:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, context-injection, P2]
related_paths:
  - ai-pic-backend/app/services/agent_core/__init__.py
  - ai-pic-backend/app/services/agent_core/context_spec.py
  - ai-pic-backend/app/services/agent_core/context_specs.py
  - ai-pic-backend/tests/unit/services/agent_core/test_context_spec.py
  - ai-pic-backend/tests/unit/services/agent_core/test_context_specs.py
  - tasks-agent-fix.md
summary: "Implemented P2.14 Context Injection Structuring with ContextSpec system"
---

## User Prompt

Continue working through the Agent optimization task list. Complete P2.14 Context Injection Structuring.

## Goals

1. Create ContextSpec system for validated context injection
2. Implement field priority and truncation strategies
3. Implement token budget aware context compression
4. Create concrete context specs for all agents
5. Add comprehensive unit tests

## Changes

### New Files Created

1. **`app/services/agent_core/context_spec.py`** (~250 lines)
   - `FieldPriority` enum: CRITICAL, HIGH, MEDIUM, LOW
   - `TruncationStrategy` enum: NONE, TAIL, HEAD, MIDDLE, SUMMARIZE
   - `FieldSpec` dataclass: Field definition with validation/transform
   - `ContextSpec` base class: Context with pack(), validate(), estimate_tokens()
   - `estimate_tokens()`: Heuristic token estimation (Chinese/English aware)
   - `truncate_text()`: Text truncation with strategy support
   - Common validators: `is_non_empty_string`, `is_non_empty_list`, `is_positive_int`
   - Common transformers: `strip_whitespace`, `normalize_newlines`

2. **`app/services/agent_core/context_specs.py`** (~230 lines)
   - `StoryContext`: 10 fields for story generation
   - `EpisodeContext`: 9 fields for episode generation
   - `ScriptContext`: 9 fields for script generation
   - `TimelineContext`: 5 fields for timeline generation
   - `StoryboardContext`: 7 fields for storyboard generation

3. **`tests/unit/services/agent_core/test_context_spec.py`** (31 tests)
   - Token estimation tests (Chinese, English, mixed)
   - Truncation strategy tests
   - FieldSpec validation/transform tests
   - ContextSpec pack/validate tests
   - Validator/transformer tests

4. **`tests/unit/services/agent_core/test_context_specs.py`** (34 tests)
   - Tests for all 5 concrete context classes
   - Required field validation tests
   - Priority and truncation behavior tests
   - Token budget scenario tests

### Updated Files

- **`app/services/agent_core/__init__.py`**: Added new exports
- **`tasks-agent-fix.md`**: Marked P2.14.1-14.4 as complete

## Validation

```bash
cd ai-pic-backend
python -m pytest tests/unit/services/agent_core/test_context_spec.py tests/unit/services/agent_core/test_context_specs.py -v
# Result: 65 passed
```

## Next Steps

1. P2.15: Quality Closed Loop Enhancement (4 subtasks)
   - 15.1: Two-layer validation (fast deterministic + deep LLM)
   - 15.2: Failure mode recognition
   - 15.3: Repair success rate monitoring
   - 15.4: Unit tests

## Linked Commits

- `0eac048` feat(backend): add context injection structuring with ContextSpec system
