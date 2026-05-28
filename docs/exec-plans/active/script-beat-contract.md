# Script Beat Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a beat-level script contract that becomes the stable structure for product script generation and provider-chain quality proof while preserving existing script API fields.

**Architecture:** Add focused schema, normalization, flattening, and validation helpers under the existing script service boundary. Integrate the helpers into the async production path first, then sync generated beats into existing `scene_beats` rows and align provider-chain harness checks with the same contract. No database migration or frontend change is included in this slice.

**Tech Stack:** FastAPI service code, Pydantic models, SQLAlchemy ORM, existing prompt templates, pytest, repository harness scripts.

---

## File Structure

- Create `ai-pic-backend/app/schemas/script_beat_contract.py`
  - Owns `StructuredScriptContract` Pydantic models and enum literals.
  - Has no database, prompt, or AI-manager dependencies.
- Create `ai-pic-backend/app/services/script/beat_contract_normalizer.py`
  - Converts contract-shaped or legacy script payloads into `StructuredScriptContract`.
  - Flattens a valid contract into legacy `scenes`, `dialogues`, `stage_directions`, and `content`.
  - Detects fallback narration/stage lines and records them as quality evidence.
- Create `ai-pic-backend/app/services/script/beat_contract_quality.py`
  - Runs deterministic structure, drama, and production checks.
  - Returns a serializable report with failed check ids and scene/beat evidence.
- Create `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
  - Tells the model to write scene beats with hook/escalation/payoff/cliffhanger fields.
- Create `ai-pic-backend/app/prompts/templates/script_beats_short_drama.yaml`
  - Metadata for the new prompt template.
- Create `ai-pic-backend/app/prompts/template_defaults.py`
  - Keeps legacy prompt defaults/examples outside the prompt enum registry so the touched registry remains within file-size limits.
- Modify `ai-pic-backend/app/prompts/templates.py`
  - Add `PromptTemplate.SCRIPT_BEATS`.
- Create `ai-pic-backend/app/services/script/beat_contract_generation.py`
  - Owns reusable beat-prompt rendering, JSON repair, normalization, and flattening for both generation paths.
- Modify `ai-pic-backend/app/services/script_agent.py`
  - Add beat-writing node after scene planning.
  - Assemble output from beat contract instead of loose dialogues.
- Modify `ai-pic-backend/app/services/ai/scripts_ai_manager.py`
  - Direct fallback uses the same beat prompt and normalizer.
- Modify `ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py`
  - Add JSON schema payload and repair hint for beat contract output.
- Modify `ai-pic-backend/app/services/script/generation_task_attempts.py`
  - Normalize, validate, and flatten generated script content before quality gate persistence.
- Modify `ai-pic-backend/app/services/script/content_normalization.py`
  - Preserve `beats` when old callers normalize a script payload.
- Modify `ai-pic-backend/app/services/script/story_structure_sync.py`
  - Create `scene_beats` rows from generated `scenes[*].beats`.
- Modify `ai-pic-backend/app/services/script_quality_gate_checks.py`
  - Add beat-contract quality report as a required script quality gate when contract data exists.
- Modify `scripts/harness/provider_chain_payloads.py`
  - Require beats in provider-chain prompt and parser.
- Modify `scripts/harness/provider_chain_timeline_payloads.py`
  - Derive dialogue/subtitle/video source text from beat contract.
- Modify `scripts/harness/production_quality_script.py`
  - Render provider-chain beat scripts into lint text and score structure from beats.
- Modify `ai-pic-backend/tests/unit/services/test_script_missing_parts.py`
  - Keep existing fallback behavior locked while making fallback evidence fail the beat gate elsewhere.
- Create `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`
  - Covers schema, flattening, legacy conversion, and fallback evidence.
- Create `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`
  - Covers structure, drama, and production gates.
- Create `ai-pic-backend/tests/unit/services/script/test_story_structure_sync_beats.py`
  - Covers syncing `scenes[*].beats` into `scene_beats`.
- Modify `ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  - Updates provider-chain harness tests to reject thin scripts and accept beat scripts.
- Modify `docs/exec-plans/active/script-beat-contract.md`
  - Check off steps as implementation progresses.

## Task 1: Add Beat Contract Schema

**Files:**

- Create: `ai-pic-backend/app/schemas/script_beat_contract.py`
- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`

- [x] **Step 1: Write schema validation tests**

Add this test file:

```python
import pytest
from pydantic import ValidationError

from app.schemas.script_beat_contract import StructuredScriptContract


def _valid_contract():
    return {
        "contract_version": "script-beat-v1",
        "title": "倒计时谜影",
        "logline": "机器人发现奖金清零，必须找出谁改了时间轴。",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "location": "控制室",
                "time_of_day": "夜",
                "estimated_duration_seconds": 15,
                "dramatic_role": "hook",
                "conflict": {
                    "question": "谁清空了奖金？",
                    "stakes": "60秒内找不到就永久丢失奖金。",
                    "opposition": "被篡改的时间轴系统。",
                    "turn": "倒计时突然启动。",
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "直接抛出损失和时间压力。",
                        "visible_event": "屏幕显示奖金归零，警报亮起。",
                        "action_lines": [
                            {"content": "小机冲到控制台，红色倒计时开始跳动。"}
                        ],
                        "dialogue_lines": [
                            {
                                "character": "小机",
                                "content": "奖金清零？",
                                "emotion": "惊慌",
                            }
                        ],
                        "duration_seconds": 5,
                        "hook_tag": "countdown_loss",
                    },
                    {
                        "order_index": 2,
                        "beat_type": "conflict",
                        "dramatic_purpose": "让主角遇到阻力。",
                        "visible_event": "修改日志被锁定，权限被拒绝。",
                        "action_lines": [{"content": "控制台弹出红色权限拒绝提示。"}],
                        "dialogue_lines": [
                            {"character": "小机", "content": "权限也没了？"}
                        ],
                        "duration_seconds": 5,
                    },
                    {
                        "order_index": 3,
                        "beat_type": "cliffhanger",
                        "dramatic_purpose": "留下未解威胁。",
                        "visible_event": "黑影从日志里删除最后一条记录。",
                        "action_lines": [{"content": "日志末行被黑色光标吞掉。"}],
                        "dialogue_lines": [
                            {"character": "小机", "content": "谁还在线？"}
                        ],
                        "duration_seconds": 5,
                        "cliffhanger_tag": "hidden_operator",
                    },
                ],
            }
        ],
    }


@pytest.mark.unit
def test_structured_script_contract_accepts_valid_payload():
    contract = StructuredScriptContract.model_validate(_valid_contract())

    assert contract.contract_version == "script-beat-v1"
    assert contract.scenes[0].beats[0].beat_type == "hook"
    assert contract.scenes[0].beats[-1].cliffhanger_tag == "hidden_operator"


@pytest.mark.unit
def test_structured_script_contract_rejects_unknown_role():
    payload = _valid_contract()
    payload["scenes"][0]["dramatic_role"] = "vibes"

    with pytest.raises(ValidationError):
        StructuredScriptContract.model_validate(payload)
```

- [x] **Step 2: Run schema tests and confirm failure**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'app.schemas.script_beat_contract'`.

- [x] **Step 3: Implement the schema**

Create `ai-pic-backend/app/schemas/script_beat_contract.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SCRIPT_BEAT_CONTRACT_VERSION = "script-beat-v1"

SceneRole = Literal["hook", "escalation", "payoff", "cliffhanger", "transition"]
BeatType = Literal[
    "hook",
    "setup",
    "conflict",
    "reveal",
    "payoff",
    "cliffhanger",
    "transition",
]


class ScriptBeatConflict(BaseModel):
    question: str = Field(..., min_length=1)
    stakes: str = Field(..., min_length=1)
    opposition: str = Field(..., min_length=1)
    turn: str | None = None


class ScriptBeatDialogueLine(BaseModel):
    character: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    emotion: str | None = None
    action: str | None = None


class ScriptBeatActionLine(BaseModel):
    content: str = Field(..., min_length=1)
    timing: str | None = None
    type: str | None = None


class ScriptBeat(BaseModel):
    order_index: int = Field(..., ge=1)
    beat_type: BeatType
    dramatic_purpose: str = Field(..., min_length=1)
    visible_event: str = Field(..., min_length=1)
    action_lines: list[ScriptBeatActionLine] = Field(default_factory=list)
    dialogue_lines: list[ScriptBeatDialogueLine] = Field(default_factory=list)
    duration_seconds: float | None = Field(None, ge=0)
    hook_tag: str | None = None
    payoff_tag: str | None = None
    cliffhanger_tag: str | None = None


class StructuredScriptScene(BaseModel):
    scene_number: int = Field(..., ge=1)
    slug_line: str = Field(..., min_length=1)
    location: str | None = None
    time_of_day: str | None = None
    estimated_duration_seconds: int | None = Field(None, ge=0)
    dramatic_role: SceneRole
    conflict: ScriptBeatConflict
    beats: list[ScriptBeat] = Field(..., min_length=1)


class StructuredScriptContract(BaseModel):
    contract_version: Literal["script-beat-v1"] = SCRIPT_BEAT_CONTRACT_VERSION
    title: str | None = None
    logline: str | None = None
    scenes: list[StructuredScriptScene] = Field(..., min_length=1)
```

- [x] **Step 4: Verify schema tests pass**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: `2 passed`.

- [x] **Step 5: Commit schema slice**

Run:

```bash
git add ai-pic-backend/app/schemas/script_beat_contract.py ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): add beat contract schema"
```

## Task 2: Add Normalizer And Flattening

**Files:**

- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_normalizer.py`

- [x] **Step 1: Add flattening and legacy-conversion tests**

Append to `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`:

```python
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)


@pytest.mark.unit
def test_flatten_contract_to_legacy_script_payload():
    contract = normalize_script_beat_contract(_valid_contract())

    flattened = flatten_contract_to_script_payload(
        contract,
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=500,
        title="倒计时谜影",
    )

    assert flattened["scenes"][0]["beats"][0]["beat_type"] == "hook"
    assert flattened["dialogues"][0]["scene_number"] == 1
    assert flattened["dialogues"][0]["character"] == "小机"
    assert flattened["stage_directions"][0]["scene_number"] == 1
    assert "小机" in flattened["content"]
    assert flattened["metadata"]["structured_contract_version"] == "script-beat-v1"


@pytest.mark.unit
def test_legacy_script_conversion_marks_fallback_evidence():
    legacy = {
        "title": "旧结构",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "summary": "小机发现奖金清零。",
            }
        ],
        "dialogues": [
            {
                "scene_number": 1,
                "character": "旁白",
                "content": "小机发现奖金清零。",
                "fallback": True,
            }
        ],
        "stage_directions": [
            {
                "scene_number": 1,
                "content": "小机发现奖金清零。",
                "type": "action",
                "fallback": True,
            }
        ],
    }

    contract = normalize_script_beat_contract(legacy)

    assert contract.scenes[0].beats[0].beat_type == "setup"
    assert contract.scenes[0].beats[0].visible_event == "小机发现奖金清零。"
    assert contract.model_extra["fallback_detected"] is True
```

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'app.services.script.beat_contract_normalizer'`.

- [x] **Step 3: Implement normalizer and flattener**

Create `ai-pic-backend/app/services/script/beat_contract_normalizer.py`:

```python
from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import (
    SCRIPT_BEAT_CONTRACT_VERSION,
    StructuredScriptContract,
)
from app.services.ai.script_text import build_script_text
from app.services.script.scene_utils import to_int


def normalize_script_beat_contract(payload: dict[str, Any]) -> StructuredScriptContract:
    if _looks_like_contract(payload):
        return StructuredScriptContract.model_validate(payload)
    return _legacy_payload_to_contract(payload)


def flatten_contract_to_script_payload(
    contract: StructuredScriptContract,
    *,
    format_type: str,
    language: str,
    episode_number: int | None,
    template_style: str | None,
    target_chars_per_episode: int | None,
    title: str | None,
) -> dict[str, Any]:
    scenes = [_scene_to_legacy(scene) for scene in contract.scenes]
    dialogues = []
    stage_directions = []
    for scene in contract.scenes:
        for beat in scene.beats:
            for line in beat.dialogue_lines:
                dialogues.append(
                    {
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "character": line.character,
                        "content": line.content,
                        "emotion": line.emotion,
                        "action": line.action,
                    }
                )
            for action in beat.action_lines:
                stage_directions.append(
                    {
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "timing": action.timing,
                        "content": action.content,
                        "type": action.type or "action",
                    }
                )
    content = build_script_text(
        scenes,
        dialogues,
        stage_directions,
        format_type=format_type,
        language=language,
        episode_number=episode_number,
        template_style=template_style,
        target_chars_per_episode=target_chars_per_episode,
        title=title or contract.title,
    )
    return {
        "content": content,
        "scenes": scenes,
        "dialogues": dialogues,
        "stage_directions": stage_directions,
        "metadata": {
            "structured_contract_version": SCRIPT_BEAT_CONTRACT_VERSION,
            "title": contract.title,
            "logline": contract.logline,
            "total_scenes": len(scenes),
            "total_dialogues": len(dialogues),
        },
        "structured_script_contract": contract.model_dump(mode="json"),
    }


def _looks_like_contract(payload: dict[str, Any]) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("contract_version") == SCRIPT_BEAT_CONTRACT_VERSION
        and isinstance(payload.get("scenes"), list)
    )


def _legacy_payload_to_contract(payload: dict[str, Any]) -> StructuredScriptContract:
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    dialogues = payload.get("dialogues") if isinstance(payload.get("dialogues"), list) else []
    stage = (
        payload.get("stage_directions")
        if isinstance(payload.get("stage_directions"), list)
        else []
    )
    fallback_detected = _has_fallback(dialogues) or _has_fallback(stage)
    converted = {
        "contract_version": SCRIPT_BEAT_CONTRACT_VERSION,
        "title": payload.get("title"),
        "logline": payload.get("logline"),
        "scenes": [],
    }
    for idx, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            scene = {"summary": str(scene)}
        scene_no = to_int(scene.get("scene_number")) or idx
        scene_dialogues = _items_for_scene(dialogues, scene_no)
        scene_stage = _items_for_scene(stage, scene_no)
        summary = (
            scene.get("summary")
            or scene.get("description")
            or scene.get("slug_line")
            or f"场景 {scene_no}"
        )
        converted["scenes"].append(
            {
                "scene_number": scene_no,
                "slug_line": scene.get("slug_line") or str(summary)[:80],
                "location": scene.get("location") or scene.get("place"),
                "time_of_day": scene.get("time_of_day") or scene.get("time"),
                "estimated_duration_seconds": to_int(
                    scene.get("estimated_duration_seconds")
                    or scene.get("duration_seconds")
                ),
                "dramatic_role": scene.get("dramatic_role") or "transition",
                "conflict": {
                    "question": scene.get("conflict_question") or str(summary),
                    "stakes": scene.get("stakes") or "本场必须推进剧情信息。",
                    "opposition": scene.get("opposition") or "阻碍尚未结构化。",
                    "turn": scene.get("turn"),
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": scene.get("beat_type") or "setup",
                        "dramatic_purpose": scene.get("notes") or str(summary),
                        "visible_event": str(summary),
                        "action_lines": [
                            {
                                "content": item.get("content")
                                or item.get("direction")
                                or str(summary),
                                "timing": item.get("timing"),
                                "type": item.get("type") or "action",
                            }
                            for item in scene_stage
                            if isinstance(item, dict)
                        ],
                        "dialogue_lines": [
                            {
                                "character": item.get("character") or "旁白",
                                "content": item.get("content")
                                or item.get("line")
                                or item.get("text")
                                or str(summary),
                                "emotion": item.get("emotion"),
                                "action": item.get("action"),
                            }
                            for item in scene_dialogues
                            if isinstance(item, dict)
                        ],
                        "duration_seconds": scene.get("estimated_duration_seconds"),
                    }
                ],
            }
        )
    contract = StructuredScriptContract.model_validate(converted)
    if fallback_detected:
        contract.model_extra["fallback_detected"] = True
    return contract


def _scene_to_legacy(scene) -> dict[str, Any]:
    return {
        "scene_number": scene.scene_number,
        "slug_line": scene.slug_line,
        "location": scene.location,
        "time_of_day": scene.time_of_day,
        "summary": scene.conflict.question,
        "description": scene.conflict.question,
        "estimated_duration_seconds": scene.estimated_duration_seconds,
        "dramatic_role": scene.dramatic_role,
        "conflict_notes": scene.conflict.model_dump(mode="json"),
        "beats": [beat.model_dump(mode="json") for beat in scene.beats],
    }


def _items_for_scene(items: list[Any], scene_no: int) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if isinstance(item, dict) and to_int(item.get("scene_number")) == scene_no
    ]


def _has_fallback(items: list[Any]) -> bool:
    return any(isinstance(item, dict) and item.get("fallback") for item in items)
```

- [x] **Step 4: Verify normalizer tests pass**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: all tests in the file pass.

- [x] **Step 5: Commit normalizer slice**

Run:

```bash
git add ai-pic-backend/app/services/script/beat_contract_normalizer.py ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): normalize beat contract payloads"
```

## Task 3: Add Deterministic Beat Quality Gates

**Files:**

- Create: `ai-pic-backend/app/services/script/beat_contract_quality.py`
- Create: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`

- [x] **Step 1: Write quality gate tests**

Create `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`:

```python
import pytest

from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_accepts_structured_contract():
    contract = normalize_script_beat_contract(_valid_contract())

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is True
    assert report["failed_checks"] == []


@pytest.mark.unit
def test_quality_gate_rejects_thin_scene_with_too_few_beats():
    payload = _valid_contract()
    payload["scenes"][0]["beats"] = payload["scenes"][0]["beats"][:1]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "scene_min_beats" in {item["check_id"] for item in report["failed_checks"]}


@pytest.mark.unit
def test_quality_gate_rejects_missing_payoff_for_multi_scene_episode():
    payload = _valid_contract()
    second = dict(payload["scenes"][0])
    second["scene_number"] = 2
    second["dramatic_role"] = "cliffhanger"
    second["beats"] = [dict(beat) for beat in payload["scenes"][0]["beats"]]
    for beat in second["beats"]:
        beat["beat_type"] = "conflict"
        beat.pop("payoff_tag", None)
    second["beats"][-1]["beat_type"] = "cliffhanger"
    second["beats"][-1]["cliffhanger_tag"] = "new_threat"
    payload["scenes"].append(second)
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "payoff_required" in {item["check_id"] for item in report["failed_checks"]}


@pytest.mark.unit
def test_quality_gate_rejects_fallback_detected_contract():
    contract = normalize_script_beat_contract(
        {
            "scenes": [{"scene_number": 1, "summary": "只有旁白"}],
            "dialogues": [
                {
                    "scene_number": 1,
                    "character": "旁白",
                    "content": "只有旁白",
                    "fallback": True,
                }
            ],
            "stage_directions": [],
        }
    )

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "fallback_content" in {item["check_id"] for item in report["failed_checks"]}
```

- [x] **Step 2: Run quality tests and confirm failure**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: fail with missing `beat_contract_quality` module.

- [x] **Step 3: Implement deterministic quality gate**

Create `ai-pic-backend/app/services/script/beat_contract_quality.py`:

```python
from __future__ import annotations

from typing import Any

from app.schemas.script_beat_contract import StructuredScriptContract


def evaluate_beat_contract_quality(
    contract: StructuredScriptContract,
    *,
    min_beats_per_scene: int = 3,
    max_dialogue_chars: int = 24,
) -> dict[str, Any]:
    failed: list[dict[str, Any]] = []

    if contract.model_extra.get("fallback_detected"):
        failed.append(_failure("fallback_content", "fallback narration cannot pass"))

    for scene in contract.scenes:
        if len(scene.beats) < min_beats_per_scene:
            failed.append(
                _failure(
                    "scene_min_beats",
                    "scene must contain at least 3 beats",
                    scene_number=scene.scene_number,
                    evidence={"beat_count": len(scene.beats)},
                )
            )
        order_indexes = [beat.order_index for beat in scene.beats]
        expected = list(range(1, len(order_indexes) + 1))
        if order_indexes != expected:
            failed.append(
                _failure(
                    "beat_order",
                    "beat order indexes must be contiguous",
                    scene_number=scene.scene_number,
                    evidence={"order_indexes": order_indexes, "expected": expected},
                )
            )
        if not any(beat.action_lines for beat in scene.beats):
            failed.append(
                _failure(
                    "scene_action_coverage",
                    "scene must include action lines",
                    scene_number=scene.scene_number,
                )
            )
        if not any(beat.dialogue_lines for beat in scene.beats):
            failed.append(
                _failure(
                    "scene_dialogue_coverage",
                    "scene must include dialogue lines",
                    scene_number=scene.scene_number,
                )
            )
        for beat in scene.beats:
            if not beat.visible_event.strip():
                failed.append(
                    _failure(
                        "beat_visible_event",
                        "beat must include a visible event",
                        scene_number=scene.scene_number,
                        beat_order_index=beat.order_index,
                    )
                )
            for line in beat.dialogue_lines:
                if _visible_len(line.content) > max_dialogue_chars:
                    failed.append(
                        _failure(
                            "dialogue_line_length",
                            "dialogue line exceeds short-drama limit",
                            scene_number=scene.scene_number,
                            beat_order_index=beat.order_index,
                            evidence={"content": line.content},
                        )
                    )

    first_scene = contract.scenes[0]
    if first_scene.beats[0].beat_type != "hook":
        failed.append(
            _failure(
                "opening_hook_required",
                "first beat of first scene must be a hook",
                scene_number=first_scene.scene_number,
                beat_order_index=first_scene.beats[0].order_index,
            )
        )

    has_escalation = any(
        scene.dramatic_role == "escalation"
        or any(beat.beat_type in {"conflict", "reveal"} for beat in scene.beats)
        for scene in contract.scenes
    )
    if not has_escalation:
        failed.append(_failure("escalation_required", "script must escalate conflict"))

    has_payoff = any(
        scene.dramatic_role == "payoff"
        or any(beat.beat_type == "payoff" or beat.payoff_tag for beat in scene.beats)
        for scene in contract.scenes
    )
    if len(contract.scenes) > 1 and not has_payoff:
        failed.append(_failure("payoff_required", "multi-scene script needs payoff"))

    final_beat = contract.scenes[-1].beats[-1]
    if final_beat.beat_type != "cliffhanger" and not final_beat.cliffhanger_tag:
        failed.append(
            _failure(
                "cliffhanger_required",
                "final beat must remain unresolved",
                scene_number=contract.scenes[-1].scene_number,
                beat_order_index=final_beat.order_index,
            )
        )

    return {
        "kind": "script_beat_contract",
        "passed": not failed,
        "failed_checks": failed,
        "check_count": 8,
    }


def _failure(
    check_id: str,
    message: str,
    *,
    scene_number: int | None = None,
    beat_order_index: int | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "message": message,
        "scene_number": scene_number,
        "beat_order_index": beat_order_index,
        "evidence": evidence or {},
    }


def _visible_len(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))
```

- [x] **Step 4: Verify quality gate tests pass**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: all tests pass.

- [x] **Step 5: Commit quality gate slice**

Run:

```bash
git add ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): validate beat contract quality"
```

## Task 4: Preserve Beats In Script Normalization

**Files:**

- Modify: `ai-pic-backend/app/services/script/content_normalization.py`
- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`

- [x] **Step 1: Add regression test for beat preservation**

Append to `ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py`:

```python
from app.services.script.content_normalization import normalize_script_content


@pytest.mark.unit
def test_content_normalization_preserves_scene_beats():
    payload = _valid_contract()
    normalized = normalize_script_content(
        payload,
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=500,
        title="倒计时谜影",
    )

    assert normalized["scenes"][0]["beats"][0]["beat_type"] == "hook"
```

- [x] **Step 2: Run test and confirm current behavior**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py::test_content_normalization_preserves_scene_beats -q
```

Expected: fail if `beats` are dropped or scene contract payload is not normalized into legacy scene fields.

- [x] **Step 3: Update content normalization**

Modify `ai-pic-backend/app/services/script/content_normalization.py` so scene construction copies beat data:

```python
        beats = base.get("beats")
        if isinstance(beats, list):
            base["beats"] = beats
        dramatic_role = base.get("dramatic_role")
        if dramatic_role:
            base["dramatic_role"] = dramatic_role
        conflict = base.get("conflict")
        if isinstance(conflict, dict):
            base["conflict"] = conflict
```

Also when building `desc`, include contract conflict question:

```python
        conflict = base.get("conflict") if isinstance(base.get("conflict"), dict) else {}
        desc = (
            base.get("description")
            or base.get("summary")
            or conflict.get("question")
            or base.get("slug_line")
            or base.get("story_beat")
            or base.get("title")
        )
```

- [x] **Step 4: Verify normalization regression**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: all tests pass.

- [x] **Step 5: Commit normalization preservation**

Run:

```bash
git add ai-pic-backend/app/services/script/content_normalization.py ai-pic-backend/tests/unit/services/script/test_beat_contract_normalizer.py docs/exec-plans/active/script-beat-contract.md
git commit -m "fix(scripts): preserve beat data during normalization"
```

## Task 5: Sync Beat Contract Into Normalized Story Structure

**Files:**

- Modify: `ai-pic-backend/app/services/script/story_structure_sync.py`
- Create: `ai-pic-backend/tests/unit/services/script/test_story_structure_sync_beats.py`

- [x] **Step 1: Write story-structure sync test**

Create `ai-pic-backend/tests/unit/services/script/test_story_structure_sync_beats.py`:

```python
from types import SimpleNamespace

import pytest

from app.services.script.story_structure_sync import sync_script_scenes_to_story_structure


@pytest.mark.unit
def test_sync_script_scenes_creates_scene_beats(monkeypatch):
    created_scene_payloads = []
    created_beat_payloads = []
    created_shots = []
    scene = SimpleNamespace(id=10, scene_number="1")

    def list_scenes_by_script(db, script_id):
        return []

    def create_scene(db, payload):
        created_scene_payloads.append(payload)
        return scene

    def create_scene_beat(db, payload):
        created_beat_payloads.append(payload)
        return SimpleNamespace(id=20, order_index=payload.order_index)

    def create_shot(db, payload):
        created_shots.append(payload)
        return SimpleNamespace(id=30)

    from app.services.script import story_structure_sync as module

    monkeypatch.setattr(module.story_structure_svc, "list_scenes_by_script", list_scenes_by_script)
    monkeypatch.setattr(module.story_structure_svc, "create_scene", create_scene)
    monkeypatch.setattr(module.story_structure_svc, "create_scene_beat", create_scene_beat)
    monkeypatch.setattr(module.story_structure_svc, "create_shot", create_shot)

    script = SimpleNamespace(
        id=1,
        scenes=[
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "summary": "谁清空了奖金？",
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "抛出损失",
                        "visible_event": "屏幕奖金归零",
                        "dialogue_lines": [{"character": "小机", "content": "奖金清零？"}],
                        "action_lines": [{"content": "红色警报亮起"}],
                        "duration_seconds": 5,
                        "hook_tag": "loss",
                    }
                ],
            }
        ],
        extra_metadata={},
    )

    result = sync_script_scenes_to_story_structure(object(), script)

    assert result["created"] == 1
    assert result["beats_created"] == 1
    assert created_beat_payloads[0].beat_type == "hook"
    assert created_beat_payloads[0].dialogue_excerpt == "小机: 奖金清零？"
    assert created_beat_payloads[0].metadata["visible_event"] == "屏幕奖金归零"
```

- [x] **Step 2: Run sync test and confirm failure**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_story_structure_sync_beats.py -q
```

Expected: fail because current sync creates scenes and placeholder shots but not `scene_beats`.

- [x] **Step 3: Extend story structure sync**

Modify `ai-pic-backend/app/services/script/story_structure_sync.py`:

```python
from app.schemas.story_structure import SceneBeatCreate, SceneCreate, ShotCreate
```

Add helper functions:

```python
def build_scene_beat_payloads(scene_raw: Any, scene_id: int) -> list[SceneBeatCreate]:
    if not isinstance(scene_raw, dict):
        return []
    beats = scene_raw.get("beats")
    if not isinstance(beats, list):
        return []
    payloads: list[SceneBeatCreate] = []
    for idx, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            continue
        order_index = to_int(beat.get("order_index")) or idx
        dialogue_excerpt = _dialogue_excerpt(beat.get("dialogue_lines"))
        payloads.append(
            SceneBeatCreate(
                scene_id=scene_id,
                order_index=order_index,
                beat_type=beat.get("beat_type"),
                beat_summary=beat.get("visible_event") or beat.get("beat_summary"),
                characters_involved=_characters_involved(beat.get("dialogue_lines")),
                dialogue_excerpt=dialogue_excerpt,
                camera_notes=beat.get("camera_notes"),
                duration_seconds=beat.get("duration_seconds"),
                metadata={
                    "dramatic_purpose": beat.get("dramatic_purpose"),
                    "visible_event": beat.get("visible_event"),
                    "hook_tag": beat.get("hook_tag"),
                    "payoff_tag": beat.get("payoff_tag"),
                    "cliffhanger_tag": beat.get("cliffhanger_tag"),
                    "action_lines": beat.get("action_lines") or [],
                    "dialogue_lines": beat.get("dialogue_lines") or [],
                },
            )
        )
    return payloads


def _dialogue_excerpt(lines: Any) -> str | None:
    if not isinstance(lines, list):
        return None
    parts = []
    for line in lines[:3]:
        if not isinstance(line, dict):
            continue
        who = line.get("character") or "旁白"
        text = line.get("content") or ""
        if text:
            parts.append(f"{who}: {text}")
    return "\n".join(parts) or None


def _characters_involved(lines: Any) -> list[str]:
    if not isinstance(lines, list):
        return []
    out: list[str] = []
    for line in lines:
        if isinstance(line, dict) and line.get("character") and line["character"] not in out:
            out.append(line["character"])
    return out
```

Inside `sync_script_scenes_to_story_structure`, keep a `(raw, created_scene)` pair and create beats after each scene:

```python
    created_pairs: list[tuple[Any, Scene]] = []
```

After creating each scene:

```python
            created_pairs.append((raw, created))
```

Then add beat creation before placeholder shots:

```python
    beats_created = 0
    for raw, scene in created_pairs:
        for beat_payload in build_scene_beat_payloads(raw, scene.id):
            try:
                story_structure_svc.create_scene_beat(db, beat_payload)
                beats_created += 1
            except Exception as exc:  # pragma: no cover - protective
                logger.warning(
                    "failed to create normalized beat for scene_id=%s: %s",
                    scene.id,
                    exc,
                )
```

Return `beats_created` in the result dict.

- [x] **Step 4: Verify sync tests pass**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_story_structure_sync_beats.py tests/test_story_structure_endpoints.py -q
```

Expected: tests pass.

- [x] **Step 5: Commit story structure sync**

Run:

```bash
git add ai-pic-backend/app/services/script/story_structure_sync.py ai-pic-backend/tests/unit/services/script/test_story_structure_sync_beats.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): sync script beats to scene beats"
```

## Task 6: Wire Beat Contract Into Script Quality Gate

**Files:**

- Modify: `ai-pic-backend/app/services/script_quality_gate_checks.py`
- Modify: `ai-pic-backend/app/services/script/generation_task_attempts.py`
- Modify: `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`

- [x] **Step 1: Add quality-gate integration test**

Append to `ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py`:

```python
from app.services.script_quality_gate_checks import beat_contract_check


@pytest.mark.unit
def test_quality_gate_check_reports_failed_beat_contract():
    contract = normalize_script_beat_contract(
        {
            "scenes": [{"scene_number": 1, "summary": "只有旁白"}],
            "dialogues": [{"scene_number": 1, "character": "旁白", "content": "只有旁白", "fallback": True}],
            "stage_directions": [],
        }
    )
    content = {"structured_script_contract": contract.model_dump(mode="json")}
    content["structured_script_contract"]["fallback_detected"] = True

    check = beat_contract_check(content)

    assert check is not None
    assert check["id"] == "script_beat_contract"
    assert check["passed"] is False
```

- [x] **Step 2: Run integration test and confirm failure**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py::test_quality_gate_check_reports_failed_beat_contract -q
```

Expected: fail because `beat_contract_check` is missing.

- [x] **Step 3: Add quality-gate check**

Modify `ai-pic-backend/app/services/script_quality_gate_checks.py`:

```python
from app.schemas.script_beat_contract import StructuredScriptContract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
```

Add:

```python
def beat_contract_check(content: Dict[str, Any]) -> Dict[str, Any] | None:
    raw = content.get("structured_script_contract")
    if not isinstance(raw, dict):
        metadata = content.get("metadata") if isinstance(content.get("metadata"), dict) else {}
        raw = metadata.get("structured_script_contract")
    if not isinstance(raw, dict):
        return None
    fallback_detected = bool(raw.pop("fallback_detected", False))
    contract = StructuredScriptContract.model_validate(raw)
    if fallback_detected:
        contract.model_extra["fallback_detected"] = True
    report = evaluate_beat_contract_quality(contract)
    return make_quality_check(
        "script_beat_contract",
        report["passed"],
        "script beat contract must pass structure and drama gates",
        details=report,
    )
```

In `evaluate_script_quality_gate`, append this check before deterministic lint:

```python
    beat_check = beat_contract_check(content)
    if beat_check:
        checks.append(beat_check)
```

- [x] **Step 4: Normalize and flatten before quality gate**

Modify `ai-pic-backend/app/services/script/generation_task_attempts.py`:

```python
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
```

After `populate_dialogues_and_stage_if_missing`, add:

```python
    try:
        beat_contract = normalize_script_beat_contract(
            {
                **ai_content,
                "scenes": scenes,
                "dialogues": dialogues,
                "stage_directions": stage_directions,
            }
        )
        flattened = flatten_contract_to_script_payload(
            beat_contract,
            format_type=request_dict.get("format_type", "screenplay"),
            language=request_dict.get("language", "zh-CN"),
            episode_number=episode.episode_number,
            template_style=request_dict.get("template_style", "commercial_vertical_drama"),
            target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
            title=episode.title,
        )
        ai_content = {**ai_content, **flattened}
        script_content = flattened["content"]
        scenes = flattened["scenes"]
        dialogues = flattened["dialogues"]
        stage_directions = flattened["stage_directions"]
    except Exception:
        # Existing quality gate still handles invalid legacy content.
        pass
```

- [x] **Step 5: Verify quality-gate tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_beat_contract_normalizer.py -q
```

Expected: tests pass.

- [x] **Step 6: Commit quality-gate integration**

Run:

```bash
git add ai-pic-backend/app/services/script_quality_gate_checks.py ai-pic-backend/app/services/script/generation_task_attempts.py ai-pic-backend/tests/unit/services/script/test_beat_contract_quality.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): gate generated scripts on beat contract"
```

## Task 7: Add Beat Prompt And LangGraph Integration

**Files:**

- Create: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`
- Create: `ai-pic-backend/app/prompts/templates/script_beats_short_drama.yaml`
- Modify: `ai-pic-backend/app/prompts/templates.py`
- Create: `ai-pic-backend/app/prompts/template_defaults.py`
- Modify: `ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py`
- Create: `ai-pic-backend/app/services/script/beat_contract_generation.py`
- Modify: `ai-pic-backend/app/services/script_agent.py`
- Modify: `ai-pic-backend/app/services/ai/scripts_ai_manager.py`

- [x] **Step 1: Add prompt template enum**

Modify `ai-pic-backend/app/prompts/templates.py`:

```python
    SCRIPT_BEATS = "script_beats"
```

Add it near the script prompt entries and map it:

```python
    PromptTemplate.SCRIPT_BEATS: PromptCategory.SCRIPT,
```

- [x] **Step 2: Add prompt templates**

Create `ai-pic-backend/app/prompts/templates/script_beats_short_drama.yaml`:

```yaml
name: script_beats_short_drama
description: "短剧 beat-level 剧本结构生成模板"
category: script
version: "1.0"
output_format: "JSON"
expected_fields:
  - contract_version
  - scenes
```

Create `ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt`:

```jinja
你是专业商用竖屏短剧结构编剧。请把场景列表展开为 beat-level 剧本合同。

硬性要求：
1. 只输出严格 JSON，不要代码块。
2. contract_version 必须是 "script-beat-v1"。
3. 每个 scene 必须有 3-5 个 beats。
4. 第一个 scene 的第一个 beat 必须是 hook。
5. 至少一个 beat 必须是 payoff，并写清主角具体赢到/得到/阻止/揭露什么。
6. 最后一个 scene 的最后一个 beat 必须是 cliffhanger 或带 cliffhanger_tag。
7. 每句对白短句为主，单句不超过 24 个可见字。
8. action_lines 必须是可拍动作/镜头/音效，不要写编剧说明。

输出结构：
{
  "contract_version": "script-beat-v1",
  "title": "...",
  "logline": "...",
  "scenes": [
    {
      "scene_number": 1,
      "slug_line": "内. 地点 - 夜",
      "location": "地点",
      "time_of_day": "夜",
      "estimated_duration_seconds": 15,
      "dramatic_role": "hook",
      "conflict": {
        "question": "本场戏剧问题",
        "stakes": "失败代价",
        "opposition": "阻力",
        "turn": "本场转折"
      },
      "beats": [
        {
          "order_index": 1,
          "beat_type": "hook",
          "dramatic_purpose": "本 beat 的戏剧目的",
          "visible_event": "观众能看见的事件",
          "action_lines": [{"content": "可拍动作", "timing": "intro", "type": "action"}],
          "dialogue_lines": [{"character": "角色", "content": "短对白", "emotion": "状态"}],
          "duration_seconds": 5,
          "hook_tag": "hook 名称"
        }
      ]
    }
  ]
}

输入 story:
{{ story | tojson }}

输入 episode:
{{ episode | tojson }}

输入 scenes:
{{ scenes | tojson }}

语言：{{ language }}
对白风格：{{ dialogue_style }}
目标正文长度：{{ target_chars_per_episode }}
特殊要求：{{ additional_requirements }}
```

- [x] **Step 3: Add JSON schema payload constants**

Modify `ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py`:

```python
_BEAT_CONTRACT_SCHEMA_PAYLOAD = {
    "name": "script_beat_contract",
    "schema": {
        "type": "object",
        "properties": {
            "contract_version": {"type": "string"},
            "title": {"type": "string"},
            "logline": {"type": "string"},
            "scenes": {"type": "array"},
        },
        "required": ["contract_version", "scenes"],
    },
}

_BEAT_CONTRACT_REPAIR_HINT = '{"contract_version":"script-beat-v1","scenes":[{"scene_number":1,"slug_line":"内. 地点 - 夜","dramatic_role":"hook","conflict":{"question":"问题","stakes":"代价","opposition":"阻力","turn":"转折"},"beats":[{"order_index":1,"beat_type":"hook","dramatic_purpose":"目的","visible_event":"可拍事件","action_lines":[{"content":"动作"}],"dialogue_lines":[{"character":"角色","content":"短对白"}]}]}]}'
_BEAT_CONTRACT_MAX_TOKENS = 6000
```

- [x] **Step 4: Plan the script-agent code edit**

In `ai-pic-backend/app/services/script_agent.py`, add a new `write_beats` node after `scene_plan` and before review/assemble. Use:

```python
prompt_manager.render_prompt(
    PromptTemplate.SCRIPT_BEATS.value,
    {
        "episode": episode,
        "story": story,
        "scenes": scenes,
        "dialogue_style": dialogue_style,
        "language": language,
        "format_type": format_type,
        "template_style": template_style,
        "target_chars_per_episode": target_chars_per_episode,
        "quality_threshold": quality_threshold,
        "additional_requirements": additional_requirements or "",
    },
)
```

The node must parse the contract, normalize it with
`normalize_script_beat_contract`, flatten it with
`flatten_contract_to_script_payload`, and return `structured_script_contract`.

- [x] **Step 5: Implement script-agent beat node**

Patch `script_agent.py` carefully around the existing graph nodes:

```python
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
```

Inside `generate`, add `write_beats`:

```python
        async def write_beats(state: Dict[str, Any]) -> Dict[str, Any]:
            if state.get("error"):
                return {**state, "reasoning": state.get("reasoning", []) + ["beats_skipped_error"]}
            scenes = state.get("scenes") or []
            prompt = prompt_manager.render_prompt(
                PromptTemplate.SCRIPT_BEATS.value,
                {
                    "episode": episode,
                    "story": story,
                    "scenes": scenes,
                    "dialogue_style": dialogue_style,
                    "language": language,
                    "format_type": format_type,
                    "template_style": template_style,
                    "target_chars_per_episode": target_chars_per_episode,
                    "quality_threshold": quality_threshold,
                    "additional_requirements": additional_requirements or "",
                },
            )
            resp = await self.service.ai_manager.generate_text(
                prompt=prompt,
                temperature=temperature,
                model=model,
                prefer_provider=prefer_provider,
                json_schema=_BEAT_CONTRACT_SCHEMA_PAYLOAD,
                system_prompt="你是专业短剧结构编剧，请严格按 JSON 返回。",
            )
            if not resp.success:
                return {"error": "beat_contract_failed", "reasoning": state.get("reasoning", []) + ["beat_contract_failed"]}
            parsed = resp.data if isinstance(resp.data, dict) else extract_json_block(str(resp.data))
            if not parsed:
                return {"error": "beat_contract_invalid_json", "raw": resp.data}
            contract = normalize_script_beat_contract(parsed)
            flattened = flatten_contract_to_script_payload(
                contract,
                format_type=format_type,
                language=language,
                episode_number=episode.get("episode_number"),
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                title=episode.get("title"),
            )
            return {
                **state,
                **flattened,
                "structured_script_contract": contract.model_dump(mode="json"),
                "reasoning": state.get("reasoning", []) + ["beat_contract_ok"],
                "provider": state.get("provider") or resp.provider,
                "model_used": state.get("model_used") or resp.model,
            }
```

Wire graph edges as:

```python
        graph.add_node("beat_contract", write_beats)
        graph.add_conditional_edges("scene_plan", end_on_error_router("beat_contract", END))
        graph.add_conditional_edges("beat_contract", end_on_error_router("react_validate", END))
```

Remove or bypass the old direct `scene_plan -> dialogue` edge only after this new edge is active.

- [x] **Step 6: Update direct AI-manager fallback**

In `ai-pic-backend/app/services/ai/scripts_ai_manager.py`, change direct fallback so it calls `SCRIPT_BEATS` after scene planning and flattens the contract. The returned `payload` must include:

```python
payload["structured_script_contract"] = contract.model_dump(mode="json")
payload["content"] = flattened["content"]
payload["scenes"] = flattened["scenes"]
payload["dialogues"] = flattened["dialogues"]
payload["stage_directions"] = flattened["stage_directions"]
payload["metadata"] = {
    **payload.get("metadata", {}),
    **flattened.get("metadata", {}),
    "structured_script_contract": contract.model_dump(mode="json"),
}
```

- [x] **Step 7: Run prompt and nearby unit tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/prompts/test_prompt_variants.py tests/unit/services/script/test_beat_contract_normalizer.py tests/unit/services/script/test_beat_contract_quality.py -q
```

Expected: tests pass.

- [x] **Step 8: Commit generation prompt slice**

Run:

```bash
git add ai-pic-backend/app/prompts/templates.py ai-pic-backend/app/prompts/templates/script_beats_short_drama.txt ai-pic-backend/app/prompts/templates/script_beats_short_drama.yaml ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py ai-pic-backend/app/services/script_agent.py ai-pic-backend/app/services/ai/scripts_ai_manager.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(scripts): generate scripts from beat contracts"
```

## Task 8: Align Provider-Chain Harness With Beat Contract

**Files:**

- Modify: `scripts/harness/provider_chain_payloads.py`
- Modify: `scripts/harness/provider_chain_timeline_payloads.py`
- Modify: `scripts/harness/production_quality_script.py`
- Modify: `ai-pic-backend/tests/scripts/test_production_quality_regression.py`

- [ ] **Step 1: Update harness tests for beat scripts**

Modify `_provider_payload()` in `ai-pic-backend/tests/scripts/test_production_quality_regression.py` so each scene includes `beats`:

```python
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "抛出异常",
                        "visible_event": "奖金清零警报亮起",
                        "dialogue": [{"speaker": "小蓝", "line": "谁动了时间轴"}],
                        "action": ["小蓝冲向控制台"],
                    },
                    {
                        "order_index": 2,
                        "beat_type": "conflict",
                        "dramatic_purpose": "增加阻力",
                        "visible_event": "权限被系统拒绝",
                        "dialogue": [{"speaker": "小蓝", "line": "权限没了"}],
                        "action": ["控制台弹出拒绝提示"],
                    },
                    {
                        "order_index": 3,
                        "beat_type": "cliffhanger",
                        "dramatic_purpose": "留下威胁",
                        "visible_event": "黑影删除日志",
                        "dialogue": [{"speaker": "小蓝", "line": "谁还在线"}],
                        "action": ["日志末行消失"],
                        "cliffhanger_tag": "hidden_operator",
                    },
                ],
```

Add a new test:

```python
def test_structured_score_rejects_thin_provider_script():
    payload = _provider_payload()
    for scene in payload["key_artifacts"]["script_payload"]["scenes"]:
        scene.pop("beats", None)

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_min_beats" in result["failed_checks"]
```

- [ ] **Step 2: Run harness tests and confirm failure**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py -q
```

Expected: fail until harness parser/scorer reads beat data.

- [ ] **Step 3: Update provider-chain prompt and parser**

Modify `scripts/harness/provider_chain_payloads.py`:

```python
        '"beats":[{"order_index":int,"beat_type":str,"dramatic_purpose":str,'
        '"visible_event":str,"action":[str],"dialogue":[{"speaker":str,"line":str}],'
        '"duration_seconds":number,"hook_tag":str,"payoff_tag":str,"cliffhanger_tag":str}],'
```

In `build_script_prompt`, add:

```python
        "Every scene must include 3 to 5 beats. The first beat of scene 1 must "
        "be hook. At least one beat across the script must be payoff. The final "
        "beat must be cliffhanger. "
```

In `extract_structured_script`, validate:

```python
        beats = scene.get("beats")
        if not isinstance(beats, list) or len(beats) < 3:
            raise ValueError(f"script_scene_{index}_missing_beats")
        for beat_index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict) or not beat.get("visible_event"):
                raise ValueError(f"script_scene_{index}_beat_{beat_index}_invalid")
```

- [ ] **Step 4: Update timeline derivation**

Modify `scripts/harness/provider_chain_timeline_payloads.py` so `dialogue_text(scene)` prefers beat dialogue:

```python
def dialogue_text(scene: dict[str, Any]) -> str:
    lines: list[str] = []
    for beat in scene.get("beats") or []:
        dialogue = beat.get("dialogue") or beat.get("dialogue_lines") or []
        for line in dialogue:
            if not isinstance(line, dict):
                continue
            speaker = line.get("speaker") or line.get("character")
            text = line.get("line") or line.get("content")
            if speaker and text:
                lines.append(f"{speaker}: {text}")
    if lines:
        return "\n".join(lines)
    return "\n".join(f"{d['speaker']}: {d['line']}" for d in scene["dialogue"])
```

In `_source_refs`, include:

```python
        "beats": scene.get("beats") or [],
```

- [ ] **Step 5: Update production quality scoring**

Modify `scripts/harness/production_quality_script.py`:

```python
def _scene_beats(scene: dict[str, Any]) -> list[dict[str, Any]]:
    beats = scene.get("beats")
    return [beat for beat in beats if isinstance(beat, dict)] if isinstance(beats, list) else []
```

Update `structured_script_score` to fail thin scripts:

```python
    failed_checks = []
    for index, scene in enumerate(scenes, start=1):
        beats = _scene_beats(scene)
        if len(beats) < 3:
            failed_checks.append("scene_min_beats")
        if any(not beat.get("visible_event") for beat in beats):
            failed_checks.append("beat_visible_event")
    has_payoff = any(
        beat.get("beat_type") == "payoff" or beat.get("payoff_tag")
        for scene in scenes
        for beat in _scene_beats(scene)
    )
    if not has_payoff:
        failed_checks.append("payoff_required")
    final_beats = _scene_beats(scenes[-1]) if scenes else []
    if final_beats and final_beats[-1].get("beat_type") != "cliffhanger" and not final_beats[-1].get("cliffhanger_tag"):
        failed_checks.append("cliffhanger_required")
```

Return:

```python
        "failed_checks": sorted(set(failed_checks)),
        "passed": not failed_checks and average >= STRUCTURED_SCORE_PASS and core_min >= STRUCTURED_CORE_MIN,
```

- [ ] **Step 6: Verify harness tests**

Run:

```bash
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: tests pass.

- [ ] **Step 7: Commit harness alignment**

Run:

```bash
git add scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline_payloads.py scripts/harness/production_quality_script.py ai-pic-backend/tests/scripts/test_production_quality_regression.py docs/exec-plans/active/script-beat-contract.md
git commit -m "feat(harness): require beat scripts in provider chain"
```

## Task 9: Run Consolidated Validation

**Files:**

- Modify: `docs/exec-plans/active/script-beat-contract.md`
- Create: `agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-script-beat-contract.md`

- [ ] **Step 1: Run focused backend and harness tests**

Run:

```bash
cd ai-pic-backend && pytest tests/unit/services/script/test_beat_contract_normalizer.py tests/unit/services/script/test_beat_contract_quality.py tests/unit/services/script/test_story_structure_sync_beats.py tests/test_script_quality_lint.py tests/test_story_structure_endpoints.py -q
pytest ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run repo docs and contract checks**

Run:

```bash
python scripts/check_repo_docs.py
python scripts/check_repo_contracts.py --mode diff ai-pic-backend/app/schemas/script_beat_contract.py ai-pic-backend/app/services/script/beat_contract_normalizer.py ai-pic-backend/app/services/script/beat_contract_quality.py ai-pic-backend/app/services/script/content_normalization.py ai-pic-backend/app/services/script/story_structure_sync.py ai-pic-backend/app/services/script/generation_task_attempts.py ai-pic-backend/app/services/script_quality_gate_checks.py ai-pic-backend/app/services/script_agent.py ai-pic-backend/app/services/ai/scripts_ai_manager.py ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py ai-pic-backend/app/prompts/templates.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_timeline_payloads.py scripts/harness/production_quality_script.py
```

Expected: both commands pass. If diff-mode reports a file-size or legacy hotspot issue, adjust the touched file split before committing.

- [ ] **Step 3: Add ledger entry**

Create a ledger file under `agent_chats/YYYY/MM/DD/` with these sections:

```markdown
## User Prompt

按要求进行分步实现

## Goals

- Implement the script beat contract in focused slices.
- Preserve existing script APIs and database schema.
- Align product generation and provider-chain quality gates.

## Changes

- Added script beat contract schemas, normalization, flattening, and deterministic quality checks.
- Wired generated beat contracts into script persistence and story-structure sync.
- Updated provider-chain script quality expectations to reject thin scripts.

## Validation

- Record exact test and check outputs from Steps 1 and 2.

## Next Steps

- Run provider-backed smoke only after provider account state is confirmed.

## Linked Commits

- List commit hashes from each completed slice.
```

- [ ] **Step 4: Run diff and pre-commit on changed files**

Run:

```bash
git diff --check
pre-commit run --files <all changed files from this plan>
```

Expected: `git diff --check` passes and pre-commit passes or only skips irrelevant no-file hooks.

- [ ] **Step 5: Commit final validation ledger**

Run:

```bash
git add docs/exec-plans/active/script-beat-contract.md agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-script-beat-contract.md
git commit -m "docs: record script beat contract validation"
```

## Self-Review

- Spec coverage:
  - Contract schema is covered by Tasks 1 and 2.
  - Structure, drama, and production gates are covered by Task 3.
  - Product production-path integration is covered by Tasks 6 and 7.
  - Existing normalized `scene_beats` sync is covered by Task 5.
  - Provider-chain alignment is covered by Task 8.
  - Repo validation and ledger discipline are covered by Task 9.
- Placeholder scan:
  - The plan does not use `TBD`, `TODO`, or "implement later".
  - Steps name exact files, commands, and expected results.
- Type consistency:
  - The contract version is consistently `script-beat-v1`.
  - The metadata key is consistently `structured_script_contract`.
  - Scene beat metadata field names match the design document.
