---
name: ai-video-studio-backend-test
description: Backend validation workflow for ai-video-studio. Use when changing FastAPI endpoints, services, repositories, models, migrations, prompts, task orchestration, or when diagnosing pytest failures. Chooses between quick, full, targeted, and diagnostic backend checks while treating AGENTS.md, ai-pic-backend/TESTING_GUIDE.md, ai-pic-backend/pytest.ini, and ai-pic-backend/tests/README.md as the source of truth.
---

# AI Video Studio Backend Test

Use this skill to choose the smallest backend validation set that still matches the risk of the change. Reuse the repo's existing commands; do not invent new wrapper scripts or treat `run_pytest.py` as the default contract.

## Read First

- `AGENTS.md`
- `docs/testing/agent-validation-workflow.md`
- `ai-pic-backend/TESTING_GUIDE.md`
- `ai-pic-backend/pytest.ini`
- `ai-pic-backend/tests/README.md`

## Command Matrix

- Quick regression for narrow service, validator, prompt, or repository changes:
  ```bash
  cd ai-pic-backend && python run_tests.py quick
  ```
- Full backend gate for migrations, auth, API shape changes, task orchestration, or pre-commit confidence:
  ```bash
  cd ai-pic-backend && pytest
  ```
- Targeted validation when touched code has a clear nearby test surface:
  ```bash
  cd ai-pic-backend && pytest <path-or-node> -v
  ```
- Diagnostic or marker-driven helper flows only when the task explicitly needs them:
  ```bash
  cd ai-pic-backend && python run_pytest.py --diagnostic
  cd ai-pic-backend && python run_pytest.py --external
  ```

## Decision Rules

- Start with targeted `pytest <path-or-node>` only when the change is isolated and the relevant tests are obvious.
- Escalate to `python run_tests.py quick` when the change affects shared utilities, serialization, prompts, or multiple backend modules.
- Escalate to full `pytest` for migrations, repository/model changes, auth, API contracts, background tasks, or whenever earlier checks fail.
- If the task mentions provider integrations or env-gated tests, read the markers in `ai-pic-backend/pytest.ini` before choosing a path.
- Treat `run_pytest.py` as an auxiliary helper for diagnostic or external-marker flows. Do not present it as the main backend entrypoint.

## Reporting Requirements

- Report the exact backend command that was run and the high-signal result.
- In `agent_chats`, record backend evidence under `## Validation` with command, scope, and outcome.
- If a lighter validation path was chosen, explain why it matched the risk.
- If a backend change affects login, UI-visible behavior, or AI/media generation, pair this skill with `ai-video-studio-mcp-e2e`.

## Explicit Invocation

Use this skill explicitly from the repo path:

```text
Use $ai-video-studio-backend-test at /Users/geyunfei/dev/yfge/ai-video-studio/.codex/skills/ai-video-studio-backend-test
```
