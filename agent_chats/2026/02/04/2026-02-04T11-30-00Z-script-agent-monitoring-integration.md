---
id: 2026-02-04T11-30-00Z-script-agent-monitoring-integration
date: 2026-02-04T11:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, agent, monitoring, refactor]
related_paths:
  - ai-pic-backend/app/services/script_agent.py
  - ai-pic-backend/app/services/agent_core/__init__.py
  - ai-pic-backend/tests/unit/services/test_script_agent_monitoring.py
summary: "Integrated Universal Agent Framework monitoring into ScriptLangGraphAgent"
---

## User Prompt

Implement P2.13.4: Script Agent Migration Plan - integrate monitoring capabilities from Universal Agent Framework into existing Script Agent while preserving its multi-stage LangGraph pipeline.

## Goals

1. Add RepairMonitor to track retry success rates in REACT validation loop
2. Add FailurePatternMatcher for error classification
3. Record repair attempts during duration validation retries
4. Include agent_metrics in generation results for observability
5. Create comprehensive unit tests for the monitoring integration
6. Ensure no regressions in existing functionality

## Changes

### `ai-pic-backend/app/services/script_agent.py`

**Added imports:**

- `time` module for duration tracking
- `FailureMode`, `FailurePatternMatcher`, `RepairMonitor` from `agent_core`

**Modified `__init__`:**

- Added `_repair_monitor = RepairMonitor(slo_threshold=0.7, window_size=100)`
- Added `_failure_matcher = FailurePatternMatcher()`

**Added `_classify_failure_mode` method:**

- Uses FailurePatternMatcher for pattern-based classification
- Falls back to script-specific heuristics for duration/dialogue/character errors
- Maps errors to standardized FailureMode enum values

**Modified `react_validate_duration` node:**

- Added timing instrumentation with `time.time()`
- Records successful repair attempts when scenes pass after retry
- Records failed attempts with classified failure modes
- Records final failures when max retries exceeded

**Modified result assembly:**

- Added `agent_metrics` dict to generation result containing:
  - `repair_success_rate`
  - `repair_attempts`
  - `successful_repairs`
  - `attempts_by_mode`
  - `attempts_by_strategy`
  - `avg_repair_duration_ms`
  - `problematic_patterns`

### `ai-pic-backend/tests/unit/services/test_script_agent_monitoring.py` (new)

Created comprehensive test suite with 18 tests covering:

- `TestScriptAgentMonitoringInit`: Verifies RepairMonitor and FailurePatternMatcher initialization
- `TestFailureModeClassification`: Tests error classification for duration, dialogue, character, reuse, and JSON errors
- `TestRepairMonitorRecording`: Tests repair attempt recording, success rate calculation, and metrics by failure mode
- `TestAgentMetricsOutput`: Tests agent_metrics structure and content
- `TestFailurePatternMatcherIntegration`: Tests pattern matching and repair hints

## Validation

### Unit Tests

```bash
cd ai-pic-backend
pytest tests/unit/services/test_script_agent_monitoring.py -v
# Result: 18 passed

pytest tests/unit/services/test_script_agent_word_count.py tests/unit/services/agent_core/test_quality_loop.py -v
# Result: 44 passed

pytest tests/unit/services/agent_core/ tests/unit/services/test_script_agent*.py -v
# Result: 195 passed, 1 skipped
```

All tests pass with no regressions.

### Code Quality

- Changes are additive only - no structural changes to LangGraph flow
- Monitoring adds <5ms overhead per validation (measured with time.time())
- New file follows existing test patterns in the codebase

## Next Steps

1. Consider adding SLO alert callback to log warnings when repair success rate drops
2. Monitor production metrics to tune SLO threshold if needed
3. Potential future work: Create optional ScriptReactAgent wrapper for simple use cases
4. Document agent_metrics schema in API documentation

## Linked Commits

- To be committed with this ledger entry
