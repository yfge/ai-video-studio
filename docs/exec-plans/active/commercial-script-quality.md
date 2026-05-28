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
