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

## Task 5: Add Character Anchoring Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`

- [x] **Step 1: Write failing character-anchor tests**

Add tests that prove beat contracts fail when dialogue uses generic role names or no named character appears across more than one beat in a scene:

```python
@pytest.mark.unit
def test_quality_gate_rejects_generic_dialogue_characters():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        for line in beat["dialogue_lines"]:
            line["character"] = "主角"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "dialogue_character_specificity" in failed
    assert "scene_protagonist_presence" in failed


@pytest.mark.unit
def test_quality_gate_requires_recurring_named_character_in_scene():
    payload = _valid_contract()
    names = ["小机", "灰屏", "黑影"]
    for beat, name in zip(payload["scenes"][0]["beats"], names, strict=True):
        beat["dialogue_lines"][0]["character"] = name
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_protagonist_presence" in failed
    assert "dialogue_character_specificity" not in failed
```

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_dialogue_characters tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_recurring_named_character_in_scene -q
```

Expected: both tests fail because the new character-specificity check ids are not emitted yet.

- [x] **Step 3: Implement minimal character-anchor helpers**

Add deterministic helper logic that rejects placeholder character names such as `角色`, `主角`, `男主`, `女主`, `人物`, `某人`, and `旁白`, then requires each multi-beat scene with dialogue to have at least one specific named character speaking in two or more beats.

- [x] **Step 4: Wire quality gate and prompt**

Emit these check ids from the beat-contract quality report:

```text
dialogue_character_specificity
scene_protagonist_presence
```

Update the short-drama beat prompt so `dialogue_lines[*].character` uses stable named characters and each scene keeps the same lead character active across multiple beats.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: all quality tests pass.

## Task 6: Validate And Commit Character Anchor Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-character-anchor.md`

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
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-character-anchor.md
git commit -m "feat(scripts): require character anchors in beat scripts"
```

## Task 7: Align Provider-Chain Character Scoring

**Files:**

- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Create: `scripts/harness/production_character_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing provider-chain character tests**

Add regression tests proving `structured_script_score` rejects provider-chain scripts with generic `speaker` names or no recurring named speaker in scene beats.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_generic_provider_dialogue_speakers ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_recurring_provider_scene_speaker -q
```

Expected: tests fail because the provider-chain structured score does not emit the character-anchor failed checks yet.

- [x] **Step 3: Add provider-chain character scoring helper**

Create `scripts/harness/production_character_score.py` with dictionary-based speaker checks for both top-level scene dialogue and beat dialogue. Emit `dialogue_character_specificity` for placeholder speakers and `scene_protagonist_presence` when no named speaker repeats in a multi-beat scene.

- [x] **Step 4: Wire scorer and prompt**

Update `production_structured_score.py` to merge character-anchor failed checks into `failed_checks`. Update `provider_chain_payloads.py` so the generation prompt explicitly forbids generic speakers such as `主角`, `角色`, `男主`, `女主`, and `旁白`.

- [x] **Step 5: Verify green**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: provider-chain quality regression tests pass.

## Task 8: Validate And Commit Provider Character Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-provider-character-anchor.md`

- [x] **Step 1: Run focused harness validation**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/scripts/test_production_quality_regression.py scripts/harness/production_character_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-provider-character-anchor.md
git commit -m "feat(harness): score provider script character anchors"
```

## Task 9: Add Beat Duration Budget Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_duration.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`

- [x] **Step 1: Write failing product duration tests**

Add tests proving beat contracts fail when estimated scenes lack beat durations or when beat duration totals do not align with the scene target.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_beat_durations_for_timed_scene tests/unit/services/script/test_quality_gate_rejects_scene_duration_mismatch -q
```

Expected: tests fail because the duration check ids do not exist yet.

- [x] **Step 3: Add duration helper and quality-gate wiring**

Create `beat_contract_duration.py` to emit `beat_duration_required` for missing or non-positive beat durations and `scene_duration_alignment` when summed beat duration differs from `scene.estimated_duration_seconds` beyond tolerance. Wire it into `beat_contract_quality.py` without growing that service past file-size limits.

- [x] **Step 4: Update prompt duration rules**

Require every timed scene to set positive `beat.duration_seconds` values whose sum matches `estimated_duration_seconds`.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: all quality tests pass.

## Task 10: Align Provider-Chain Duration Scoring

**Files:**

- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Modify: `ai-pic-backend/tests/scripts/provider_chain_fixtures.py`
- Create: `scripts/harness/production_duration_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing provider-chain duration tests**

Add tests proving provider-chain structured scoring rejects scripts with missing beat durations or beat totals that do not align with scene duration.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_provider_beat_durations ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_provider_scene_duration_mismatch -q
```

Expected: tests fail because provider-chain duration checks do not exist yet.

- [x] **Step 3: Add provider-chain duration scorer**

Create `production_duration_score.py` to read dictionary-shaped scenes and beats, emit `beat_duration_required` for missing or invalid beat durations, and emit `scene_duration_alignment` when beat totals do not map to scene `duration_seconds`.

- [x] **Step 4: Wire scorer, fixtures, and prompt**

Update `production_structured_score.py` to merge duration checks, update provider-chain fixtures with valid beat durations, and update the provider prompt to require beat duration sums.

- [x] **Step 5: Verify green**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: provider-chain quality regression tests pass.

## Task 11: Validate And Commit Duration Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-duration-budget.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_duration.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/provider_chain_fixtures.py scripts/harness/production_duration_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-duration-budget.md
git commit -m "feat(scripts): enforce beat duration budgets"
```

## Task 12: Add Filmable Action Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`

- [x] **Step 1: Write failing product filmability tests**

Add a test proving beat contracts fail when `visible_event` and `action_lines` describe internal states or abstract emotion rather than visible screen behavior.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_internal_state_as_visible_action -q
```

Expected: the test fails because the existing specificity check does not reject internal-state wording yet.

- [x] **Step 3: Extend product specificity helper**

Update `beat_contract_specificity.py` so `is_specific_text` rejects internal-state and abstract-causality wording such as `意识到`, `明白`, `感到`, `内心`, `情绪`, `命运`, and `关系变化` when used as visible/action text.

- [x] **Step 4: Update short-drama prompt**

Tell the model that `visible_event` and `action_lines` must name a visible object, gesture, movement, screen change, sound, or physical result, and must not use internal-state wording.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: all quality tests pass.

## Task 13: Align Provider-Chain Filmability Scoring

**Files:**

- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Create: `scripts/harness/production_filmability_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing provider-chain filmability tests**

Add a test proving provider-chain structured scoring rejects internal-state `visible_event` and `action` wording.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_internal_state_provider_beats -q
```

Expected: the test fails because provider-chain structured scoring does not inspect event/action filmability yet.

- [x] **Step 3: Add provider-chain filmability scorer**

Create `production_filmability_score.py` that emits `beat_visible_event_specificity` and `beat_action_specificity` for internal-state or abstract beat text.

- [x] **Step 4: Wire scorer and prompt**

Update `production_structured_score.py` to merge filmability failed checks, and update `provider_chain_payloads.py` to forbid internal-state visible events/actions.

- [x] **Step 5: Verify green**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: provider-chain quality regression tests pass.

## Task 14: Validate And Commit Filmability Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-filmable-script-actions.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_quality_regression.py scripts/harness/production_filmability_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-filmable-script-actions.md
git commit -m "feat(scripts): reject unfilmable beat actions"
```

## Task 15: Add Dialogue Substance Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`

- [x] **Step 1: Write failing product dialogue-substance test**

Add a test proving beat contracts fail when all dialogue lines are filler such as `好的`.

- [x] **Step 2: Run test and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_filler_dialogue_lines -q
```

Expected: the test fails because filler dialogue currently passes.

- [x] **Step 3: Add dialogue-substance helper**

Extend `beat_contract_specificity.py` to emit `dialogue_substance` when a dialogue line is a filler acknowledgement or when every dialogue line in a scene is too thin to carry story information.

- [x] **Step 4: Wire product gate and prompt**

Update `beat_contract_quality.py` to merge dialogue-substance issues and update the short-drama prompt to forbid filler-only dialogue.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: all quality tests pass.

## Task 16: Align Provider-Chain Dialogue Scoring

**Files:**

- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Create: `scripts/harness/production_dialogue_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing provider-chain dialogue test**

Add a test proving provider-chain structured scoring rejects filler-only scene and beat dialogue.

- [x] **Step 2: Run test and confirm red**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_filler_provider_dialogue -q
```

Expected: the test fails because provider-chain structured scoring does not inspect dialogue substance yet.

- [x] **Step 3: Add provider-chain dialogue scorer**

Create `production_dialogue_score.py` to emit `dialogue_substance` for filler-only provider-chain dialogue.

- [x] **Step 4: Wire scorer and prompt**

Update `production_structured_score.py` to merge dialogue failed checks, and update `provider_chain_payloads.py` to forbid filler-only dialogue.

- [x] **Step 5: Verify green**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: provider-chain quality regression tests pass.

## Task 17: Validate And Commit Dialogue Substance Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dialogue-substance.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_quality_regression.py scripts/harness/production_dialogue_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dialogue-substance.md
git commit -m "feat(scripts): reject filler-only beat dialogue"
```

## Task 18: Add Protagonist Screen-Presence Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Modify: `scripts/harness/production_character_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add regressions proving a script fails when the recurring named protagonist speaks across a scene but never appears in `visible_event` or `action_lines` / `action`.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_requires_protagonist_in_screen_action -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_requires_provider_protagonist_in_screen_action -q
```

Expected: both tests fail because `scene_protagonist_screen_presence` is not emitted yet.

- [x] **Step 3: Add screen-presence helpers**

Extend the product beat-contract specificity helper and provider-chain character scorer so a recurring named speaker must appear in beat-level screen action text.

- [x] **Step 4: Wire quality gates and prompts**

Emit `scene_protagonist_screen_presence` from product and provider scoring. Update prompts so model output puts the named protagonist into visible beat actions instead of only dialogue.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: selected product and provider quality tests pass.

## Task 19: Validate And Commit Protagonist Screen-Presence Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-protagonist-screen-presence.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_quality_regression.py scripts/harness/production_character_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-protagonist-screen-presence.md
git commit -m "feat(scripts): require protagonist screen presence"
```

## Task 20: Add Dramatic-Purpose Specificity Gates

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_purpose.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
- Create: `scripts/harness/production_purpose_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add regressions proving a beat contract or provider script fails when every beat uses a generic `dramatic_purpose` such as `推进剧情`.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_generic_dramatic_purpose -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py::test_structured_score_rejects_generic_provider_beat_purpose -q
```

Expected: both tests fail because `beat_dramatic_purpose_specificity` is not emitted yet.

- [x] **Step 3: Add dramatic-purpose scorers**

Create focused product and provider helpers that reject vague purpose phrases such as `推进剧情`, `制造悬念`, `制造冲突`, and `出现转折`.

- [x] **Step 4: Wire quality gates and prompts**

Emit `beat_dramatic_purpose_specificity` from product and provider scoring. Update prompts so model output names the concrete story turn, clue, choice, threat, or result for each beat.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: selected product and provider quality tests pass.

## Task 21: Validate And Commit Dramatic-Purpose Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dramatic-purpose.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_purpose.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_quality_regression.py scripts/harness/production_purpose_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dramatic-purpose.md
git commit -m "feat(scripts): require concrete beat purposes"
```

## Task 22: Add Beat Progression Repetition Gates

**Files:**

- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_progression_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_progression.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Create: `ai-pic-backend/tests/scripts/test_production_progression_score.py`
- Create: `scripts/harness/production_progression_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add focused regressions proving a script fails when every beat in a scene repeats the same `visible_event` plus action screen state.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_progression_quality.py::test_quality_gate_rejects_repeated_screen_beats -q
pytest ai-pic-backend/tests/scripts/test_production_progression_score.py::test_structured_score_rejects_repeated_provider_screen_beats -q
```

Expected: both tests fail because `beat_progression_repetition` is not emitted yet.

- [x] **Step 3: Add progression scorers**

Create focused product and provider helpers that detect duplicate beat screen states within the same scene.

- [x] **Step 4: Wire quality gates and prompts**

Emit `beat_progression_repetition` from product and provider scoring. Update prompts so model output creates distinct screen states or new information for each beat.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_progression_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_progression_score.py -q
```

Expected: selected product and provider progression tests pass.

## Task 23: Validate And Commit Beat Progression Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-beat-progression.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_progression_quality.py ai-pic-backend/app/services/script/beat_contract_progression.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_progression_score.py scripts/harness/production_progression_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-beat-progression.md
git commit -m "feat(scripts): reject repeated beat progression"
```

## Task 24: Require Payoff In Every Script Contract

**Files:**

- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_payoff_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`
- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`

- [x] **Step 1: Write failing single-scene payoff test**

Add a focused regression proving a single-scene script without any payoff beat or payoff tag fails with `payoff_required`.

- [x] **Step 2: Run test and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_payoff_quality.py::test_quality_gate_requires_payoff_for_single_scene_script -q
```

Expected: the test fails because product quality currently requires payoff only for multi-scene scripts.

- [x] **Step 3: Tighten product payoff gate**

Update `evaluate_beat_contract_quality()` so every script contract requires a payoff, matching the existing prompt and provider-chain structured scorer.

- [x] **Step 4: Update valid fixture**

Update `_valid_contract()` to include a concrete payoff tag and visible payoff evidence, then adjust missing-payoff tests to remove payoff from all scenes.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_payoff_quality.py::test_quality_gate_requires_payoff_for_single_scene_script tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_accepts_structured_contract tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_rejects_missing_payoff_for_multi_scene_episode -q
```

Expected: selected product payoff tests pass.

## Task 25: Validate And Commit Payoff Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-payoff.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_payoff_quality.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-script-payoff.md
git commit -m "feat(scripts): require payoff in beat scripts"
```

## Task 26: Add Dialogue Progression Gates

**Files:**

- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_dialogue_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_dialogue.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Create: `ai-pic-backend/tests/scripts/test_production_dialogue_score.py`
- Modify: `scripts/harness/production_dialogue_score.py`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add focused regressions proving a script fails when all beat dialogue lines in one scene repeat the same non-filler sentence.

- [x] **Step 2: Run tests and confirm red**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py::test_quality_gate_rejects_repeated_dialogue_lines -q
pytest ai-pic-backend/tests/scripts/test_production_dialogue_score.py::test_structured_score_rejects_repeated_provider_dialogue_lines -q
```

Expected: both tests fail because `dialogue_progression_repetition` is not emitted yet.

- [x] **Step 3: Add dialogue progression helpers**

Move product dialogue substance checks into a focused `beat_contract_dialogue.py` helper and add repeated-line detection. Extend provider-chain dialogue scoring with the same check id.

- [x] **Step 4: Wire quality gates and prompts**

Emit `dialogue_progression_repetition` from product and provider scoring. Update prompts so model output avoids repeating the same dialogue line within one scene.

- [x] **Step 5: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_dialogue_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_dialogue_score.py -q
```

Expected: selected product and provider dialogue progression tests pass.

## Task 27: Validate And Commit Dialogue Progression Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dialogue-progression.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: selected backend and harness tests pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_dialogue_quality.py ai-pic-backend/app/services/script/beat_contract_dialogue.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_dialogue_score.py scripts/harness/production_dialogue_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-dialogue-progression.md
git commit -m "feat(scripts): reject repeated dialogue beats"
```

## Task 28: Add Scene Question-Turn Specificity Gates

**Files:**

- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_conflict_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_conflict.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Create: `ai-pic-backend/tests/scripts/test_production_conflict_score.py`
- Create: `scripts/harness/production_conflict_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `ai-pic-backend/tests/scripts/provider_chain_fixtures.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add regressions proving the product beat-contract quality gate and provider structured score reject scenes without a concrete dramatic question and scene turn.

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py::test_quality_gate_requires_scene_question_and_turn -q
pytest ai-pic-backend/tests/scripts/test_production_conflict_score.py::test_structured_score_requires_provider_scene_question_and_turn -q
```

Expected: both tests fail because question/turn specificity is not scored yet.

- [x] **Step 2: Add focused conflict helpers**

Move product scene-conflict quality checks into `beat_contract_conflict.py`, then add concrete `question` and `turn` checks. Add a provider conflict scorer that emits the same check ids from provider-chain scene payloads.

- [x] **Step 3: Wire quality gates and prompts**

Emit `scene_conflict_question` and `scene_conflict_turn` from product and provider scoring. Update prompts and provider fixtures so generated scripts carry one concrete scene question and one concrete scene turn per scene.

- [x] **Step 4: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: selected product and provider conflict tests pass.

## Task 29: Validate And Commit Scene Question-Turn Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-scene-question-turn.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: focused backend and provider harness suites pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_conflict_quality.py ai-pic-backend/app/services/script/beat_contract_conflict.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/provider_chain_fixtures.py scripts/harness/production_conflict_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-scene-question-turn.md
git commit -m "feat(scripts): require scene question turns"
```

## Task 30: Reject Resolved Final Cliffhangers

**Files:**

- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_cliffhanger_quality.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_cliffhanger.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Modify: `ai-pic-backend/app/services/script/beat_contract_specificity.py`
- Create: `ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py`
- Create: `scripts/harness/production_cliffhanger_score.py`
- Modify: `scripts/harness/production_structured_score.py`
- Modify: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Modify: `scripts/harness/provider_chain_payloads.py`

- [x] **Step 1: Write failing product and provider tests**

Add regressions proving a final beat cannot pass merely by being labelled `cliffhanger` if the screen text resolves the story with completion, restored safety, or full reward recovery.

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_cliffhanger_quality.py::test_quality_gate_rejects_resolved_final_cliffhanger -q
pytest ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py::test_structured_score_rejects_resolved_provider_final_cliffhanger -q
```

Expected: both tests fail because resolved final cliffhangers are not scored yet.

- [x] **Step 2: Add focused cliffhanger helpers**

Move product final cliffhanger specificity into `beat_contract_cliffhanger.py` and add resolution-phrase detection. Add a provider scorer that emits the same `cliffhanger_unresolved_threat` check id.

- [x] **Step 3: Wire quality gates and prompts**

Emit `cliffhanger_unresolved_threat` from product and provider scoring. Update prompts so final beats must end on a visible unresolved threat, unanswered question, countdown, deletion, arrival, or object change rather than full resolution.

- [x] **Step 4: Verify green**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_quality.py -q
pytest ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: selected product and provider cliffhanger tests pass.

## Task 31: Validate And Commit Final Cliffhanger Slice

**Files:**

- Modify: `docs/exec-plans/active/commercial-script-quality.md`
- Create: `agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-final-cliffhanger.md`

- [x] **Step 1: Run focused validation**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_cliffhanger_quality.py tests/unit/services/script/test_beat_contract_conflict_quality.py tests/unit/services/script/test_beat_contract_dialogue_quality.py tests/unit/services/script/test_beat_contract_payoff_quality.py tests/unit/services/script/test_beat_contract_purpose_quality.py tests/unit/services/script/test_beat_contract_progression_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py ai-pic-backend/tests/scripts/test_production_conflict_score.py ai-pic-backend/tests/scripts/test_production_dialogue_score.py ai-pic-backend/tests/scripts/test_production_progression_score.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: focused backend and provider harness suites pass.

- [x] **Step 2: Run repo docs and diff contracts**

Run:

```bash
python scripts/check_repo_docs.py
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff
```

Expected: both commands pass.

- [x] **Step 3: Add ledger entry**

Create a ledger file with the repository-required sections and exact validation output.

- [x] **Step 4: Run whitespace and targeted pre-commit checks**

Run:

```bash
git diff --check
{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files
```

Expected: diff check passes and pre-commit passes with backend pytest skipped only for the documented local MySQL default issue.

- [x] **Step 5: Commit the slice**

Run:

```bash
git add ai-pic-backend/tests/unit/services/script/test_beat_contract_cliffhanger_quality.py ai-pic-backend/app/services/script/beat_contract_cliffhanger.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/beat_contract_specificity.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/tests/scripts/test_production_cliffhanger_score.py scripts/harness/production_cliffhanger_score.py scripts/harness/production_structured_score.py scripts/harness/provider_chain_payloads.py docs/exec-plans/active/commercial-script-quality.md agent_chats/2026/05/28/YYYY-MM-DDTHH-MM-SSZ-final-cliffhanger.md
git commit -m "feat(scripts): reject resolved cliffhangers"
```
