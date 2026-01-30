# Duration Orchestrator Agent Guide

## Overview

The Duration Orchestrator Agent is a LangGraph-based system that ensures episode dialogue timing matches target duration requirements through scene-level closed-loop validation.

## Core Problem

When generating episode dialogue:
- Episode Agent estimates duration (`estimated_duration_seconds`) using LLM
- TTS actual duration can differ by 50%+ from estimates
- Script Agent doesn't know target scene duration, so dialogue length is random
- Timeline Agent can only make minor adjustments with gaps, can't fix large deviations

## Solution: Scene-Level Closed-Loop Validation

The Duration Orchestrator:
1. **Allocates budget** - Distributes total episode duration across scenes
2. **Generates dialogue** - Creates dialogue with word count constraints
3. **Validates timing** - Measures actual TTS duration
4. **Retries if needed** - Regenerates if timing is off (max 3 retries)
5. **Rebalances** - Adjusts remaining scene budgets after each commit

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Duration Orchestrator Agent                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  allocate_budget                                            │
│       ↓                                                     │
│  generate_dialogue ←────────────────────┐                   │
│       ↓                                 │                   │
│  tts_trial                              │                   │
│       ↓                                 │                   │
│  validate_duration                      │                   │
│       ↓                                 │                   │
│  ┌────┴────┐                            │                   │
│  │         │                            │                   │
│  commit  prepare_retry ─────────────────┘                   │
│  │                                                          │
│  ↓                                                          │
│  ┌────┴────┐                                                │
│  │         │                                                │
│  continue  assemble_episode                                 │
│  (loop)         ↓                                           │
│           final_validation                                  │
│                 ↓                                           │
│                END                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Node Details

### 1. allocate_budget

Distributes total episode duration across scenes based on importance weights.

**Input State:**
- `total_duration_minutes`: Target episode length
- `scenes_from_episode`: Scene list from Episode Agent

**Output State:**
- `scene_budgets`: List of `SceneBudget` with target duration and word count
- `buffer_seconds`: Reserved buffer time
- `remaining_budget_seconds`: Remaining allocatable time

**Logging:**
```python
logger.info("allocate_budget_node", extra={
    "episode_id": episode_id,
    "total_duration_minutes": total_duration_minutes,
    "scene_count": len(scenes),
    "event": "budget_allocated"
})
```

### 2. generate_dialogue

Generates scene dialogue with word count constraints using Script Agent.

**Input State:**
- `scene_budgets`: Scene budgets with word count targets
- `current_scene_index`: Current scene being processed

**Output State:**
- `generated_dialogues`: Dict mapping scene_id to dialogue
- `generation_attempts`: Retry count per scene

**Word Count Calculation:**
```python
# Chinese: ~4 characters/second
# English: ~2.5 words/second
target_word_count = target_duration_seconds * chars_per_second
```

### 3. tts_trial

Measures actual dialogue duration using TTS estimation or real TTS.

**Modes:**
- **Estimation mode** (default): Uses character count heuristics
- **Actual TTS mode**: Calls TTS service for precise measurement

**Output State:**
- `measured_durations`: Dict mapping scene_id to actual duration

### 4. validate_duration

Validates measured duration against target (±15% tolerance).

**Validation Rules:**
- `actual / target` within [0.85, 1.15] → PASS
- Outside tolerance → FAIL, trigger retry

**Output State:**
- `validation_results`: Dict with pass/fail status per scene
- `duration_deviation`: Percentage deviation from target

### 5. commit_scene / prepare_retry

**commit_scene:**
- Marks scene as completed
- Triggers budget rebalancing for remaining scenes
- Advances to next scene

**prepare_retry:**
- Generates adjustment hints ("add 2 lines, ~50 chars")
- Increments retry count
- Returns to generate_dialogue

### 6. assemble_episode

Combines all committed scene dialogues into final episode structure.

**Output State:**
- `final_dialogues`: Merged dialogue list
- `final_duration_seconds`: Total episode duration

### 7. final_validation

Validates total episode duration (±10% tolerance).

**Success Criteria:**
- Total duration within ±10% of target
- All scenes committed successfully

## Usage

### Basic Usage

```python
from app.services.duration_orchestrator import DurationOrchestratorAgent

agent = DurationOrchestratorAgent(
    script_agent=script_agent,
    tts_service=None,  # Use estimation mode
    use_actual_tts=False,
)

result = await agent.run(
    episode_id=123,
    total_duration_minutes=3,
    scenes_from_episode=scenes,
)
```

### With Progress Callbacks

```python
def on_progress(event: str, data: dict):
    print(f"Progress: {event} - {data}")

result = await agent.run(
    episode_id=123,
    total_duration_minutes=3,
    scenes_from_episode=scenes,
    progress_callback=on_progress,
)
```

### API Integration

The Duration Orchestrator is integrated into the dialogue-audio generation endpoint:

```http
POST /api/v1/scripts/{script_id}/dialogue-audio/generate-async
{
    "use_duration_control": true,
    "total_duration_minutes": 3
}
```

## Configuration

### Constants (`constants.py`)

```python
# Timing tolerances
SCENE_TOLERANCE = 0.15  # ±15% per scene
EPISODE_TOLERANCE = 0.10  # ±10% for episode

# Retry limits
MAX_SCENE_RETRIES = 3

# Word count estimation
CHARS_PER_SECOND_ZH = 4.0
WORDS_PER_SECOND_EN = 2.5

# Buffer allocation
BUFFER_PERCENTAGE = 0.05  # 5% buffer
```

## Acceptance Criteria

| Metric | Target |
|--------|--------|
| Scene duration deviation | ≤ ±15% |
| Episode total deviation | ≤ ±10% |
| Average retries per scene | ≤ 1.5 |
| End-to-end generation time | ≤ existing flow × 1.5 |
| Unit test coverage | ≥ 80% |

## Troubleshooting

### Common Issues

1. **All retries exhausted**
   - Check if scene has unrealistic duration target
   - Consider splitting long scenes

2. **TTS estimation inaccurate**
   - Enable actual TTS mode for production
   - Calibrate `CHARS_PER_SECOND` for your TTS provider

3. **Budget allocation unbalanced**
   - Adjust scene importance weights
   - Review `allocate_scene_budgets` logic

### Logging

Enable debug logging:
```python
import logging
logging.getLogger("app.services.duration_orchestrator").setLevel(logging.DEBUG)
```

Key log events:
- `budget_allocated`: Budget distribution complete
- `dialogue_generated`: Scene dialogue generated
- `duration_validated`: Duration check result
- `scene_committed`: Scene locked
- `episode_assembled`: Final assembly complete

## Related Documentation

- [Timeline Rendering Pipeline](./timeline-rendering-pipeline.md)
- [Dialogue Audio Timeline Spec](./dialogue-audio-timeline-spec.md)
