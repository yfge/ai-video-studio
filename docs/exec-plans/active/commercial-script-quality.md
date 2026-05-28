# Commercial Script Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make beat-level script contracts reject structurally valid but commercially vague short-drama scripts.

**Architecture:** Extend the existing deterministic beat-contract quality service with commercial specificity checks instead of adding a new scoring system. Keep the contract schema and persistence shape unchanged; improve prompt instructions so model output targets the same checks that local validation enforces.

**Tech Stack:** FastAPI service code, Pydantic beat-contract models, prompt templates, pytest, repository docs and contract checks.

---

## File Structure

- Modify `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
  - Adds regression coverage for generic, abstract, and placeholder beat contracts.
- Modify `ai-pic-backend/app/services/script/beat_contract_quality.py`
  - Adds deterministic commercial specificity checks for conflict, visible events, action lines, payoff, and final cliffhanger.
- Create `ai-pic-backend/app/services/script/beat_contract_specificity.py`
  - Keeps commercial-specificity heuristics out of the quality service file-size limit.
- Modify `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
  - Adds prompt-side rules that match the deterministic checks.
- Modify `docs/exec-plans/active/commercial-script-quality.md`
  - Tracks this implementation slice.
- Modify `docs/README.md`
  - Registers this active execution plan.
- Create `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-commercial-script-quality.md`
  - Records prompt, goals, changes, validation, risks, and commit linkage.

## Task 1: Document Active Plan

**Files:**

- Create: `docs/exec-plans/active/commercial-script-quality.md`
- Modify: `docs/README.md`

- [x] **Step 1: Save this plan**

Create this document under `docs/exec-plans/active/` with the goal, architecture, file map, and executable tasks.

- [x] **Step 2: Register the active plan**

Add this row to `docs/README.md` under the active execution plans list:

```markdown
- `docs/exec-plans/active/commercial-script-quality.md` — deterministic
  commercial-specificity gate for beat-level short-drama scripts.
```

## Task 2: Add Failing Commercial Specificity Tests

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`

- [x] **Step 1: Write the failing regression tests**

Add tests that start from `_valid_contract()` and prove these weak contracts fail:

```python
@pytest.mark.unit
def test_quality_gate_rejects_generic_conflict_and_abstract_beats():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["conflict"]["stakes"] = "主角面临重大危机。"
    scene["conflict"]["opposition"] = "神秘力量阻止他。"
    for beat in scene["beats"]:
        beat["visible_event"] = "剧情继续推进。"
        beat["action_lines"] = [{"content": "角色开始行动。"}]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_conflict_specificity" in failed
    assert "beat_visible_event_specificity" in failed
    assert "beat_action_specificity" in failed


@pytest.mark.unit
def test_quality_gate_rejects_symbolic_payoff_and_empty_cliffhanger():
    payload = _valid_contract()
    beats = payload["scenes"][0]["beats"]
    beats[1]["beat_type"] = "payoff"
    beats[1]["payoff_tag"] = "win"
    beats[1]["visible_event"] = "主角获得胜利。"
    beats[-1]["beat_type"] = "cliffhanger"
    beats[-1]["cliffhanger_tag"] = "suspense"
    beats[-1]["visible_event"] = "留下巨大悬念。"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "payoff_specificity" in failed
    assert "cliffhanger_specificity" in failed
```

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_conflict_and_abstract_beats tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_symbolic_payoff_and_empty_cliffhanger -q
```

Expected: both tests fail because the new commercial-specificity check ids are not emitted yet.

## Task 3: Implement Commercial Specificity Gate

**Files:**

- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`

- [x] **Step 1: Add minimal deterministic helpers**

Add helper functions that classify vague phrases, concrete text, scene conflict specificity, beat event/action specificity, payoff specificity, and cliffhanger specificity. Keep helpers in `beat_contract_specificity.py` and avoid schema changes.

- [x] **Step 2: Wire helpers into scene and beat validation**

Emit these check ids:

```text
scene_conflict_specificity
beat_visible_event_specificity
beat_action_specificity
payoff_specificity
cliffhanger_specificity
```

- [x] **Step 3: Update prompt constraints**

Add prompt rules requiring stakes/opposition, visible events, actions, payoff, and cliffhanger to include concrete objects, actions, threats, or results rather than generic phrases.

- [x] **Step 4: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: all quality tests pass.

## Task 4: Validate And Commit

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-commercial-script-quality.md`

- [x] **Step 1: Run focused backend validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: selected tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode diff $(git diff --name-only main...HEAD)
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections:

```markdown
## User Prompt

commit

## Goals

- Continue moving generated scripts toward commercial short-drama quality.
- Reject structurally valid but vague beat contracts.

## Changes

- Record exact changes from this slice.

## Validation

- Record exact command outcomes from Steps 1 and 2.

## Next Steps

- Note any remaining provider-backed or browser validation that was not run.

## Linked Commits

- Pending until commit is created.
```

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
SKIP=backend-pytest pre-commit run --files $(git diff --name-only main...HEAD)
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only if the repo-local MySQL default remains unavailable.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt docs/exec-plans/active/commercial-script-quality.md docs/README.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-commercial-script-quality.md
git commit -m "feat(scripts): tighten commercial beat quality"
```

## Self-Review

- Spec coverage:
  - Vague conflict, abstract visible events, generic action lines, symbolic payoff, and empty cliffhanger are all covered by Task 2 and Task 3.
  - Existing schema and persistence compatibility are preserved because no model or database fields are changed.
  - Prompt and deterministic gate stay aligned.
- Placeholder scan:
  - This plan has no `TBD`, `TODO`, or implementation-later placeholders.
- Type consistency:
  - All tests use existing `script-beat-v1` contract fields and existing `failed_checks[*].check_id` output.
